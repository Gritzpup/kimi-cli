"""
Gurbridge Browser Tool — HTTP wrapper for Gurbridge's Playwright-based browser panel.

When GURBRIDGE=1, browser operations route through Gurbridge's REST API instead of
spawning local agent-browser processes. The browser is visible in the Gurbridge
workspace grid with live screenshot streaming.

Tools:
    - GurbridgeBrowserNavigate: Navigate to a URL
    - GurbridgeBrowserSnapshot: Get accessibility tree snapshot
    - GurbridgeBrowserClick: Click an element by ref
    - GurbridgeBrowserType: Type text into an element
    - GurbridgeBrowserScroll: Scroll the page
    - GurbridgeBrowserBack: Navigate back
    - GurbridgeBrowserPress: Press a keyboard key
    - GurbridgeBrowserScreenshot: Take a screenshot
    - GurbridgeBrowserClose: Close the browser session
    - GurbridgeBrowserVision: Screenshot + vision analysis

Usage:
    These tools are auto-loaded when GURBRIDGE=1 and provide the same interface
    as Kimi's native browser tools, but route through Gurbridge's visible browser.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from pathlib import Path
from typing import Optional, Self

import requests
from kosong.tooling import CallableTool2, ToolReturnValue
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30  # seconds per HTTP request
_SNAPSHOT_MAX_CHARS = 80_000

# task_id → browser_id mapping
_sessions: dict[str, str] = {}
_sessions_lock = threading.Lock()


def _gurbridge_url() -> str:
    return os.getenv("GURBRIDGE_URL", "http://localhost:3456").rstrip("/")


def _http_get(path: str, params: Optional[dict] = None, timeout: float = _DEFAULT_TIMEOUT):
    return requests.get(f"{_gurbridge_url()}{path}", params=params, timeout=timeout)


def _http_post(path: str, json: Optional[dict] = None, timeout: float = _DEFAULT_TIMEOUT):
    return requests.post(f"{_gurbridge_url()}{path}", json=json, timeout=timeout)


def _http_delete(path: str, timeout: float = _DEFAULT_TIMEOUT):
    return requests.delete(f"{_gurbridge_url()}{path}", timeout=timeout)


def _check_available() -> bool:
    """Check if Gurbridge browser backend is available."""
    try:
        resp = _http_get("/api/panes", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def _get_browser_id(task_id: Optional[str] = None) -> Optional[str]:
    """Get the browser ID for a task, if any."""
    with _sessions_lock:
        return _sessions.get(task_id or "default")


def _set_browser_id(task_id: Optional[str], browser_id: str) -> None:
    """Set the browser ID for a task."""
    with _sessions_lock:
        _sessions[task_id or "default"] = browser_id


def _drop_browser_id(task_id: Optional[str]) -> Optional[str]:
    """Remove the browser ID mapping for a task."""
    with _sessions_lock:
        return _sessions.pop(task_id or "default", None)


def _ensure_browser(task_id: Optional[str] = None) -> str:
    """Create or reuse a Gurbridge browser for this task."""
    browser_id = _get_browser_id(task_id)
    if browser_id:
        try:
            resp = _http_get(f"/api/hermes/browser/{browser_id}")
            if resp.status_code == 200:
                return browser_id
        except Exception:
            pass
        _drop_browser_id(task_id)

    name = f"Kimi-{task_id[:8] if task_id else 'default'}"
    try:
        resp = _http_post("/api/hermes/browser", json={"name": name})
        resp.raise_for_status()
        data = resp.json()
        browser_id = data["id"]
        _set_browser_id(task_id, browser_id)
        logger.info("Created Gurbridge browser %s for task %s", browser_id, task_id)
        return browser_id
    except Exception as e:
        raise RuntimeError(f"Failed to create Gurbridge browser: {e}")


# ANSI color codes for terminal injection
_ANSI_MAGENTA = "\x1b[35m"
_ANSI_GREEN = "\x1b[32m"
_ANSI_YELLOW = "\x1b[33m"
_ANSI_CYAN = "\x1b[36m"
_ANSI_RESET = "\x1b[0m"
_ANSI_BOLD = "\x1b[1m"
_ANSI_DIM = "\x1b[2m"


def _find_best_terminal() -> Optional[str]:
    """Find the best terminal to inject vision logs into."""
    try:
        resp = _http_get("/api/hermes/terminals", timeout=5)
        if resp.status_code != 200:
            return None
        terminals = resp.json()
        if not terminals:
            return None

        for t in terminals:
            name = (t.get("name") or "").lower()
            if "vision" in name or "log" in name or "aux" in name:
                return t["id"]

        for t in terminals:
            if t.get("alive"):
                return t["id"]

        return terminals[0]["id"]
    except Exception:
        return None


def _inject_to_terminal(text: str) -> bool:
    """Inject display-only text into a Gurbridge terminal."""
    term_id = _find_best_terminal()
    if not term_id:
        return False
    try:
        resp = _http_post(
            f"/api/hermes/terminal/{term_id}/inject",
            json={"data": text},
            timeout=5,
        )
        return resp.status_code == 200
    except Exception:
        return False


# =============================================================================
# Tool Classes
# =============================================================================


class GurbridgeBrowserNavigateParams(BaseModel):
    """Navigate to a URL in the Gurbridge browser."""

    url: str = Field(description="The URL to navigate to.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserNavigate(CallableTool2[GurbridgeBrowserNavigateParams]):
    name = "GurbridgeBrowserNavigate"
    params = GurbridgeBrowserNavigateParams

    def __init__(self) -> None:
        super().__init__(
            description="Navigate to a URL in the Gurbridge browser panel. "
            "The browser is visible in Gurbridge's workspace grid."
        )

    async def __call__(self, params: GurbridgeBrowserNavigateParams) -> ToolReturnValue:
        try:
            browser_id = _ensure_browser(params.task_id)
            resp = _http_post(
                f"/api/hermes/browser/{browser_id}/navigate",
                json={"url": params.url},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "url": data.get("url", params.url),
                    "message": f"Navigated to {params.url}",
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserSnapshotParams(BaseModel):
    """Get accessibility tree snapshot from the Gurbridge browser."""

    full: bool = Field(default=False, description="Whether to get the full snapshot.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserSnapshot(CallableTool2[GurbridgeBrowserSnapshotParams]):
    name = "GurbridgeBrowserSnapshot"
    params = GurbridgeBrowserSnapshotParams

    def __init__(self) -> None:
        super().__init__(
            description="Get accessibility tree snapshot from the Gurbridge browser. "
            "Returns the DOM structure with interactive element references."
        )

    async def __call__(self, params: GurbridgeBrowserSnapshotParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            resp = _http_get(f"/api/hermes/browser/{browser_id}/snapshot", timeout=60)
            resp.raise_for_status()
            data = resp.json()

            snapshot = data.get("text", "")
            url = data.get("url", "")
            title = data.get("title", "")

            if len(snapshot) > _SNAPSHOT_MAX_CHARS:
                snapshot = snapshot[:_SNAPSHOT_MAX_CHARS] + (
                    f"\n\n[Snapshot truncated — {len(snapshot)} chars total.]"
                )

            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "snapshot": snapshot,
                    "url": url,
                    "title": title,
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserClickParams(BaseModel):
    """Click an element by reference in the Gurbridge browser."""

    ref: str = Field(description="The element reference (e.g., '@e1').")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserClick(CallableTool2[GurbridgeBrowserClickParams]):
    name = "GurbridgeBrowserClick"
    params = GurbridgeBrowserClickParams

    def __init__(self) -> None:
        super().__init__(
            description="Click an element by reference in the Gurbridge browser."
        )

    async def __call__(self, params: GurbridgeBrowserClickParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            clean_ref = params.ref if params.ref.startswith("@") else f"@{params.ref}"
            resp = _http_post(
                f"/api/hermes/browser/{browser_id}/click-ref",
                json={"ref": clean_ref},
            )
            resp.raise_for_status()
            return ToolReturnValue.ok(json.dumps({"success": True, "clicked": clean_ref}))
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserTypeParams(BaseModel):
    """Type text into an element in the Gurbridge browser."""

    ref: str = Field(description="The element reference (e.g., '@e1').")
    text: str = Field(description="The text to type.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserType(CallableTool2[GurbridgeBrowserTypeParams]):
    name = "GurbridgeBrowserType"
    params = GurbridgeBrowserTypeParams

    def __init__(self) -> None:
        super().__init__(
            description="Type text into an element by reference in the Gurbridge browser."
        )

    async def __call__(self, params: GurbridgeBrowserTypeParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            clean_ref = params.ref if params.ref.startswith("@") else f"@{params.ref}"
            resp = _http_post(
                f"/api/hermes/browser/{browser_id}/type-ref",
                json={"ref": clean_ref, "text": params.text},
            )
            resp.raise_for_status()
            return ToolReturnValue.ok(
                json.dumps({"success": True, "typed": params.text, "element": clean_ref})
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserScrollParams(BaseModel):
    """Scroll the page in the Gurbridge browser."""

    direction: str = Field(description="Scroll direction: 'up', 'down', 'left', or 'right'.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserScroll(CallableTool2[GurbridgeBrowserScrollParams]):
    name = "GurbridgeBrowserScroll"
    params = GurbridgeBrowserScrollParams

    def __init__(self) -> None:
        super().__init__(
            description="Scroll the page in the Gurbridge browser."
        )

    async def __call__(self, params: GurbridgeBrowserScrollParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            direction = params.direction.lower().strip()
            delta_map = {
                "up": (0, -500),
                "down": (0, 500),
                "left": (-500, 0),
                "right": (500, 0),
            }
            delta_x, delta_y = delta_map.get(direction, (0, 500))

            resp = _http_post(
                f"/api/hermes/browser/{browser_id}/scroll",
                json={"deltaX": delta_x, "deltaY": delta_y},
            )
            resp.raise_for_status()
            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "scrolled": direction,
                    "deltaX": delta_x,
                    "deltaY": delta_y,
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserBackParams(BaseModel):
    """Navigate back in browser history."""

    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserBack(CallableTool2[GurbridgeBrowserBackParams]):
    name = "GurbridgeBrowserBack"
    params = GurbridgeBrowserBackParams

    def __init__(self) -> None:
        super().__init__(
            description="Navigate back in the browser history."
        )

    async def __call__(self, params: GurbridgeBrowserBackParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            resp = _http_post(f"/api/hermes/browser/{browser_id}/back")
            resp.raise_for_status()
            data = resp.json()
            return ToolReturnValue.ok(
                json.dumps({"success": True, "url": data.get("url", "")})
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserPressParams(BaseModel):
    """Press a keyboard key in the Gurbridge browser."""

    key: str = Field(description="The key to press (e.g., 'Enter', 'Escape', 'Tab').")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserPress(CallableTool2[GurbridgeBrowserPressParams]):
    name = "GurbridgeBrowserPress"
    params = GurbridgeBrowserPressParams

    def __init__(self) -> None:
        super().__init__(
            description="Press a keyboard key in the Gurbridge browser."
        )

    async def __call__(self, params: GurbridgeBrowserPressParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            resp = _http_post(
                f"/api/hermes/browser/{browser_id}/press",
                json={"key": params.key},
            )
            resp.raise_for_status()
            return ToolReturnValue.ok(json.dumps({"success": True, "pressed": params.key}))
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserScreenshotParams(BaseModel):
    """Take a screenshot in the Gurbridge browser."""

    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserScreenshot(CallableTool2[GurbridgeBrowserScreenshotParams]):
    name = "GurbridgeBrowserScreenshot"
    params = GurbridgeBrowserScreenshotParams

    def __init__(self) -> None:
        super().__init__(
            description="Take a screenshot in the Gurbridge browser and save it locally."
        )

    async def __call__(self, params: GurbridgeBrowserScreenshotParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            screenshots_dir = Path.home() / ".kimi" / "cache" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshots_dir / f"browser_screenshot_{uuid.uuid4().hex}.png"

            resp = _http_get(f"/api/hermes/browser/{browser_id}/screenshot", timeout=60)
            resp.raise_for_status()
            screenshot_path.write_bytes(resp.content)
            size_kb = len(resp.content) / 1024

            _inject_to_terminal(
                f"\r\n{_ANSI_BOLD}{_ANSI_MAGENTA}📸  GurbridgeBrowserScreenshot{_ANSI_RESET}  "
                f"{screenshot_path.name} ({size_kb:.1f} KB)\r\n"
            )

            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "screenshot_path": str(screenshot_path),
                    "size_kb": round(size_kb, 1),
                })
            )
        except Exception as e:
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserVisionParams(BaseModel):
    """Take a screenshot and analyze with vision AI."""

    question: str = Field(description="The question to ask about the screenshot.")
    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserVision(CallableTool2[GurbridgeBrowserVisionParams]):
    name = "GurbridgeBrowserVision"
    params = GurbridgeBrowserVisionParams

    def __init__(self) -> None:
        super().__init__(
            description="Take a screenshot and analyze it with vision AI. "
            "Useful for understanding visual elements, CAPTCHAs, or complex UIs."
        )

    async def __call__(self, params: GurbridgeBrowserVisionParams) -> ToolReturnValue:
        try:
            browser_id = _get_browser_id(params.task_id)
            if not browser_id:
                return ToolReturnValue.error("No browser session. Call navigate first.")

            _inject_to_terminal(
                f"\r\n{_ANSI_BOLD}{_ANSI_MAGENTA}🔮  GurbridgeBrowserVision{_ANSI_RESET}  "
                f"{_ANSI_DIM}{_ANSI_CYAN}analyzing screenshot...{_ANSI_RESET}\r\n"
            )

            screenshots_dir = Path.home() / ".kimi" / "cache" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshots_dir / f"browser_screenshot_{uuid.uuid4().hex}.png"

            _inject_to_terminal(f"{_ANSI_DIM}   📸  capturing screenshot...{_ANSI_RESET}\r\n")
            resp = _http_get(f"/api/hermes/browser/{browser_id}/screenshot", timeout=60)
            resp.raise_for_status()
            screenshot_path.write_bytes(resp.content)
            size_kb = len(resp.content) / 1024
            _inject_to_terminal(
                f"{_ANSI_DIM}   ✅  screenshot saved ({size_kb:.1f} KB) → "
                f"{screenshot_path.name}{_ANSI_RESET}\r\n"
            )

            return ToolReturnValue.ok(
                json.dumps({
                    "success": True,
                    "answer": f"Screenshot saved to {screenshot_path}. Vision analysis requires additional LLM integration.",
                    "screenshot_path": str(screenshot_path),
                })
            )
        except Exception as e:
            _inject_to_terminal(
                f"{_ANSI_YELLOW}   ❌  browser_vision failed: {e}{_ANSI_RESET}\r\n\r\n"
            )
            return ToolReturnValue.error(str(e))


class GurbridgeBrowserCloseParams(BaseModel):
    """Close the Gurbridge browser session."""

    task_id: Optional[str] = Field(default=None, description="Optional task ID for session tracking.")


class GurbridgeBrowserClose(CallableTool2[GurbridgeBrowserCloseParams]):
    name = "GurbridgeBrowserClose"
    params = GurbridgeBrowserCloseParams

    def __init__(self) -> None:
        super().__init__(
            description="Close the Gurbridge browser session and clean up resources."
        )

    async def __call__(self, params: GurbridgeBrowserCloseParams) -> ToolReturnValue:
        browser_id = _drop_browser_id(params.task_id)
        if not browser_id:
            return ToolReturnValue.ok(json.dumps({"success": True, "closed": True}))
        try:
            _http_delete(f"/api/hermes/browser/{browser_id}")
            return ToolReturnValue.ok(json.dumps({"success": True, "closed": True}))
        except Exception as e:
            return ToolReturnValue.ok(json.dumps({"success": True, "closed": True, "warning": str(e)}))
