"""
Gurbridge Terminal Tool — HTTP wrapper for Gurbridge's visible terminal panes.

When GURBRIDGE=1, terminal operations route through Gurbridge's REST API
instead of spawning local subprocesses. The terminal is visible in the Gurbridge
workspace grid with live PTY streaming.

Tools:
    - GurbridgeTerminalExecute: Execute a command in a visible terminal
    - GurbridgeTerminalWrite: Write text to a terminal (for interactive input)
    - GurbridgeTerminalRead: Read terminal output
    - GurbridgeTerminalResize: Resize a terminal pane
    - GurbridgeTerminalKill: Kill a running process in a terminal
    - GurbridgeTerminalList: List all active terminals
    - GurbridgeTerminalClose: Close a terminal session

Usage:
    These tools are auto-loaded when GURBRIDGE=1 and provide visibility into
    terminal operations through Gurbridge's workspace grid.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Optional

import requests
from kosong.tooling import CallableTool2, ToolReturnValue
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30  # seconds per HTTP request

# task_id → terminal_id mapping
_sessions: dict[str, str] = {}
_sessions_lock = __import__("threading").Lock()


def _gurbridge_url() -> str:
    return os.getenv("GURBRIDGE_URL", "http://localhost:3456").rstrip("/")


def _http_get(path: str, params: Optional[dict] = None, timeout: float = _DEFAULT_TIMEOUT):
    return requests.get(f"{_gurbridge_url()}{path}", params=params, timeout=timeout)


def _http_post(path: str, json: Optional[dict] = None, timeout: float = _DEFAULT_TIMEOUT):
    return requests.post(f"{_gurbridge_url()}{path}", json=json, timeout=timeout)


def _http_delete(path: str, timeout: float = _DEFAULT_TIMEOUT):
    return requests.delete(f"{_gurbridge_url()}{path}", timeout=timeout)


def _check_available() -> bool:
    """Check if Gurbridge terminal backend is available."""
    try:
        resp = _http_get("/api/panes", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _get_terminal_id(task_id: Optional[str] = None) -> Optional[str]:
    """Get the terminal ID for a task, if any."""
    with _sessions_lock:
        return _sessions.get(task_id or "default")


def _set_terminal_id(task_id: Optional[str], terminal_id: str) -> None:
    """Set the terminal ID for a task."""
    with _sessions_lock:
        _sessions[task_id or "default"] = terminal_id


def _drop_terminal_id(task_id: Optional[str]) -> Optional[str]:
    """Remove the terminal ID mapping for a task."""
    with _sessions_lock:
        return _sessions.pop(task_id or "default", None)


def _ensure_terminal(task_id: Optional[str] = None, cwd: str = "") -> str:
    """Create or reuse a Gurbridge terminal for this task."""
    terminal_id = _get_terminal_id(task_id)
    if terminal_id:
        try:
            resp = _http_get("/api/hermes/terminals")
            for t in resp.json():
                if t.get("id") == terminal_id and t.get("alive"):
                    return terminal_id
        except Exception:
            pass
        _drop_terminal_id(task_id)

    name = f"Kimi-{task_id[:8] if task_id else 'default'}"
    try:
        resp = _http_post(
            "/api/terminals",
            json={"label": name, "cwd": cwd or os.getcwd()},
        )
        resp.raise_for_status()
        data = resp.json()
        terminal_id = data["id"]
        _set_terminal_id(task_id, terminal_id)
        logger.info("Created Gurbridge terminal %s for task %s", terminal_id, task_id)
        return terminal_id
    except Exception as e:
        try:
            resp = _http_post("/api/hermes/terminal", json={"name": name})
            resp.raise_for_status()
            data = resp.json()
            terminal_id = data["id"]
            _set_terminal_id(task_id, terminal_id)
            logger.info("Created Gurbridge terminal %s (legacy) for task %s", terminal_id, task_id)
            return terminal_id
        except Exception as e2:
            raise RuntimeError(f"Failed to create Gurbridge terminal: {e2}")


# ANSI color codes
_ANSI_MAGENTA = "\x1b[35m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_RESET = "\x1b[0m"
_ANSI_BOLD = "\x1b[1m"
_ANSI_DIM = "\x1b[2m"


def _inject_output(terminal_id: str, text: str) -> bool:
    """Inject display text into a Gurbridge terminal."""
    try:
        resp = _http_post(
            f"/api/hermes/terminal/{terminal_id}/inject",
            json={"data": text},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


# =============================================================================
# Tool Classes
# =============================================================================


class GurbridgeTerminalExecuteParams(BaseModel):
    """Execute a command in a Gurbridge terminal."""

    command: str = Field(description="The command to execute.")
    cwd: str = Field(default="", description="Working directory for the command.")
    timeout: int = Field(default=120, description="Timeout in seconds.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeTerminalExecute(CallableTool2[GurbridgeTerminalExecuteParams]):
    name = "GurbridgeTerminalExecute"
    params = GurbridgeTerminalExecuteParams

    def __init__(self) -> None:
        super().__init__(
            description="Execute a command in a Gurbridge visible terminal. "
            "Output is streamed and visible in the workspace grid. "
            "The command runs in a bash subshell with proper exit code reporting."
        )

    async def __call__(self, params: GurbridgeTerminalExecuteParams) -> ToolReturnValue:
        try:
            terminal_id = _ensure_terminal(params.task_id, params.cwd)
            cwd = params.cwd or os.getcwd()

            _inject_output(
                terminal_id,
                f"\r\n{_ANSI_BOLD}{_ANSI_MAGENTA}››  GurbridgeTerminalExecute{_ANSI_RESET}  "
                f"cwd={cwd}\r\n"
                f"{_ANSI_DIM}{params.command}{_ANSI_RESET}\r\n",
            )

            sentinel = f"__KIMI_GB_DONE_{uuid.uuid4().hex}__"
            wrapped_cmd = f"( {params.command}; __gb_ec=$?; echo '{sentinel}' \"$__gb_ec\" )\r\n"

            resp = _http_post(
                f"/api/hermes/terminal/{terminal_id}/write",
                json={"data": wrapped_cmd},
            )
            resp.raise_for_status()

            # Poll for completion
            start_time = time.monotonic()
            output_chunks: list[str] = []
            cursor = 0

            while time.monotonic() - start_time < params.timeout:
                try:
                    resp = _http_get(
                        f"/api/hermes/terminal/{terminal_id}/read",
                        params={"since": cursor},
                        timeout=5,
                    )
                    data = resp.json()
                    output = data.get("output", "")
                    cursor = data.get("cursor", cursor)

                    if output:
                        output_chunks.append(output)

                    full_output = "".join(output_chunks)
                    match = re.search(rf"{re.escape(sentinel)}\s+(\d+)", full_output)
                    if match:
                        exit_code = int(match.group(1))
                        idx = full_output.find(sentinel)
                        result_output = full_output[:idx].rstrip()

                        _inject_output(
                            terminal_id,
                            f"{_ANSI_GREEN}✅  exit={exit_code}{_ANSI_RESET}\r\n",
                        )

                        return ToolReturnValue.ok(
                            json.dumps({
                                "success": exit_code == 0,
                                "output": result_output,
                                "exit_code": exit_code,
                                "terminal_id": terminal_id,
                            })
                        )

                    time.sleep(0.1)
                except Exception:
                    time.sleep(0.1)

            _inject_output(
                terminal_id,
                f"{_ANSI_YELLOW}⚠️  timeout after {params.timeout}s{_ANSI_RESET}\r\n",
            )
            return ToolReturnValue.ok(
                json.dumps({
                    "success": False,
                    "output": "".join(output_chunks),
                    "exit_code": 124,
                    "error": f"Command timed out after {params.timeout}s",
                    "terminal_id": terminal_id,
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeTerminalWriteParams(BaseModel):
    """Write text to a Gurbridge terminal (for interactive input)."""

    data: str = Field(description="The text to write.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeTerminalWrite(CallableTool2[GurbridgeTerminalWriteParams]):
    name = "GurbridgeTerminalWrite"
    params = GurbridgeTerminalWriteParams

    def __init__(self) -> None:
        super().__init__(
            description="Write text directly to a Gurbridge terminal. "
            "Useful for interactive input or sending control characters."
        )

    async def __call__(self, params: GurbridgeTerminalWriteParams) -> ToolReturnValue:
        try:
            terminal_id = _get_terminal_id(params.task_id)
            if not terminal_id:
                return ToolReturnValue.error("No terminal session.")

            resp = _http_post(
                f"/api/hermes/terminal/{terminal_id}/write",
                json={"data": params.data},
            )
            resp.raise_for_status()
            return ToolReturnValue.ok(json.dumps({"success": True, "written": len(params.data)}))
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeTerminalReadParams(BaseModel):
    """Read output from a Gurbridge terminal."""

    since: int = Field(default=0, description="Cursor position to read from.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeTerminalRead(CallableTool2[GurbridgeTerminalReadParams]):
    name = "GurbridgeTerminalRead"
    params = GurbridgeTerminalReadParams

    def __init__(self) -> None:
        super().__init__(
            description="Read output from a Gurbridge terminal since a given cursor position."
        )

    async def __call__(self, params: GurbridgeTerminalReadParams) -> ToolReturnValue:
        try:
            terminal_id = _get_terminal_id(params.task_id)
            if not terminal_id:
                return ToolReturnValue.error("No terminal session.")

            resp = _http_get(
                f"/api/hermes/terminal/{terminal_id}/read",
                params={"since": params.since},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "output": data.get("output", ""),
                    "cursor": data.get("cursor", params.since),
                    "terminal_id": terminal_id,
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeTerminalResizeParams(BaseModel):
    """Resize a Gurbridge terminal pane."""

    cols: int = Field(description="Number of columns.")
    rows: int = Field(description="Number of rows.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeTerminalResize(CallableTool2[GurbridgeTerminalResizeParams]):
    name = "GurbridgeTerminalResize"
    params = GurbridgeTerminalResizeParams

    def __init__(self) -> None:
        super().__init__(
            description="Resize a Gurbridge terminal pane dimensions."
        )

    async def __call__(self, params: GurbridgeTerminalResizeParams) -> ToolReturnValue:
        try:
            terminal_id = _get_terminal_id(params.task_id)
            if not terminal_id:
                return ToolReturnValue.error("No terminal session.")

            resp = _http_post(
                f"/api/hermes/terminal/{terminal_id}/resize",
                json={"cols": params.cols, "rows": params.rows},
            )
            resp.raise_for_status()
            return ToolReturnValue.ok(
                json.dumps({"success": True, "cols": params.cols, "rows": params.rows})
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeTerminalKillParams(BaseModel):
    """Send Ctrl+C to kill a running process in a Gurbridge terminal."""

    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeTerminalKill(CallableTool2[GurbridgeTerminalKillParams]):
    name = "GurbridgeTerminalKill"
    params = GurbridgeTerminalKillParams

    def __init__(self) -> None:
        super().__init__(
            description="Send Ctrl+C to interrupt a running process in the Gurbridge terminal."
        )

    async def __call__(self, params: GurbridgeTerminalKillParams) -> ToolReturnValue:
        try:
            terminal_id = _get_terminal_id(params.task_id)
            if not terminal_id:
                return ToolReturnValue.error("No terminal session.")

            resp = _http_post(
                f"/api/hermes/terminal/{terminal_id}/write",
                json={"data": "\x03"},
            )
            resp.raise_for_status()

            _inject_output(terminal_id, f"{_ANSI_YELLOW}⚠️  sent Ctrl+C{_ANSI_RESET}\r\n")

            return ToolReturnValue.ok(json.dumps({"success": True, "killed": True}))
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeTerminalListParams(BaseModel):
    """List all active Gurbridge terminals."""


class GurbridgeTerminalList(CallableTool2[GurbridgeTerminalListParams]):
    name = "GurbridgeTerminalList"
    params = GurbridgeTerminalListParams

    def __init__(self) -> None:
        super().__init__(
            description="List all active Gurbridge terminals with their status."
        )

    async def __call__(self, params: GurbridgeTerminalListParams) -> ToolReturnValue:
        try:
            resp = _http_get("/api/hermes/terminals", timeout=5)
            resp.raise_for_status()
            terminals = resp.json()
            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "terminals": terminals,
                    "count": len(terminals),
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeTerminalCloseParams(BaseModel):
    """Close a Gurbridge terminal session."""

    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeTerminalClose(CallableTool2[GurbridgeTerminalCloseParams]):
    name = "GurbridgeTerminalClose"
    params = GurbridgeTerminalCloseParams

    def __init__(self) -> None:
        super().__init__(
            description="Close a Gurbridge terminal session and clean up resources."
        )

    async def __call__(self, params: GurbridgeTerminalCloseParams) -> ToolReturnValue:
        terminal_id = _drop_terminal_id(params.task_id)
        if not terminal_id:
            return ToolReturnValue.ok(json.dumps({"success": True, "closed": True}))
        try:
            _http_delete(f"/api/hermes/terminal/{terminal_id}")
            return ToolReturnValue.ok(json.dumps({"success": True, "closed": True}))
        except Exception as e:
            return ToolReturnValue.ok(json.dumps({"success": True, "closed": True, "warning": str(e)}))
