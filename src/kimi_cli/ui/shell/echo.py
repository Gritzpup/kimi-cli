from __future__ import annotations

from kosong.message import Message
from rich.text import Text

from kimi_cli.skin_engine import get_active_prompt_symbol
from kimi_cli.utils.message import message_stringify


def render_user_echo(message: Message) -> Text:
    """Render a user message as literal shell transcript text."""
    prompt_symbol = get_active_prompt_symbol("✨ ")
    return Text(f"{prompt_symbol}{message_stringify(message)}")


def render_user_echo_text(text: str) -> Text:
    """Render the local prompt text exactly as the user saw it in the buffer."""
    prompt_symbol = get_active_prompt_symbol("✨ ")
    return Text(f"{prompt_symbol}{text}")
