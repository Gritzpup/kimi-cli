"""
Gurbridge Tools Package

Provides HTTP wrapper tools that route browser and terminal operations through
Gurbridge's visible workspace panels when GURBRIDGE=1.

Tools:
    - browser.py: GurbridgeBrowserNavigate, GurbridgeBrowserSnapshot, etc.
    - terminal.py: GurbridgeTerminalExecute, GurbridgeTerminalWrite, etc.

These tools mirror the hermes browser_gurbridge.py and terminal_tool.py patterns
but are adapted for Kimi's tool framework.
"""

from kimi_cli.tools.gurbridge.browser import (
    gurbridge_navigate,
    gurbridge_snapshot,
    gurbridge_click,
    gurbridge_type,
    gurbridge_scroll,
    gurbridge_back,
    gurbridge_press,
    gurbridge_screenshot,
    gurbridge_vision,
    gurbridge_close,
    gurbridge_hover,
    gurbridge_highlight,
    gurbridge_get_html,
    gurbridge_get_text,
    gurbridge_set_viewport,
)

from kimi_cli.tools.gurbridge.terminal import (
    gurbridge_terminal_execute,
    gurbridge_terminal_write,
    gurbridge_terminal_read,
    gurbridge_terminal_resize,
    gurbridge_terminal_kill,
    gurbridge_terminal_list,
    gurbridge_terminal_close,
)

__all__ = [
    # Browser tools
    "gurbridge_navigate",
    "gurbridge_snapshot",
    "gurbridge_click",
    "gurbridge_type",
    "gurbridge_scroll",
    "gurbridge_back",
    "gurbridge_press",
    "gurbridge_screenshot",
    "gurbridge_vision",
    "gurbridge_close",
    "gurbridge_hover",
    "gurbridge_highlight",
    "gurbridge_get_html",
    "gurbridge_get_text",
    "gurbridge_set_viewport",
    # Terminal tools
    "gurbridge_terminal_execute",
    "gurbridge_terminal_write",
    "gurbridge_terminal_read",
    "gurbridge_terminal_resize",
    "gurbridge_terminal_kill",
    "gurbridge_terminal_list",
    "gurbridge_terminal_close",
]
