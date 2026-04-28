"""Kimi CLI skin/theme engine.

A data-driven skin system that lets users customize the CLI's visual appearance.
Skins are defined as YAML files in ~/.kimi/skins/ or as built-in presets.

BUILT-IN SKINS
==============

- ``default`` — Classic Kimi gold/blue
- ``gurbridge`` — Gurbridge IDE theme (teal/cyan)
- ``sisyphus`` — Austere grayscale with persistence
- ``ares`` — Crimson/bronze war-god theme
- ``mono`` — Clean grayscale monochrome
- ``slate`` — Cool blue developer-focused theme
- ``daylight`` — Light theme for bright terminals
- ``charizard`` — Volcanic theme (burnt orange and ember)

USER SKINS
==========

Drop a YAML file in ``~/.kimi/skins/<name>.yaml`` following the schema from
Hermes skin_engine. Activate with the ``KIMI_SKIN`` environment variable.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Skin data structure
# =============================================================================


@dataclass
class SkinConfig:
    """Complete skin configuration."""

    name: str
    description: str = ""
    colors: Dict[str, str] = field(default_factory=dict)
    spinner: Dict[str, Any] = field(default_factory=dict)
    branding: Dict[str, str] = field(default_factory=dict)
    tool_prefix: str = "│"
    tool_emojis: Dict[str, str] = field(default_factory=dict)
    banner_logo: str = ""  # Rich-markup ASCII art logo
    banner_hero: str = ""  # Rich-markup hero art

    def get_color(self, key: str, fallback: str = "") -> str:
        """Get a color value with fallback."""
        return self.colors.get(key, fallback)

    def get_spinner_wings(self) -> List[Tuple[str, str]]:
        """Get spinner wing pairs, or empty list if none."""
        raw = self.spinner.get("wings", [])
        result = []
        for pair in raw:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                result.append((str(pair[0]), str(pair[1])))
        return result

    def get_branding(self, key: str, fallback: str = "") -> str:
        """Get a branding value with fallback."""
        return self.branding.get(key, fallback)


# =============================================================================
# Built-in skin definitions (port from Hermes skin_engine)
# =============================================================================

_BUILTIN_SKINS: Dict[str, Dict[str, Any]] = {
    "default": {
        "name": "default",
        "description": "Classic Kimi — gold and blue",
        "colors": {
            "banner_border": "#CD7F32",
            "banner_title": "#FFD700",
            "banner_accent": "#FFBF00",
            "banner_dim": "#B8860B",
            "banner_text": "#FFF8DC",
            "ui_accent": "#FFBF00",
            "ui_label": "#DAA520",
            "ui_ok": "#4caf50",
            "ui_error": "#ef5350",
            "ui_warn": "#ffa726",
            "prompt": "#FFF8DC",
            "input_rule": "#CD7F32",
            "response_border": "#FFD700",
            "status_bar_bg": "#1a1a2e",
            "status_bar_text": "#C0C0C0",
            "status_bar_strong": "#FFD700",
            "status_bar_dim": "#8B8682",
            "status_bar_good": "#8FBC8F",
            "status_bar_warn": "#FFD700",
            "status_bar_bad": "#FF8C00",
            "status_bar_critical": "#FF6B6B",
            "session_label": "#DAA520",
            "session_border": "#8B8682",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Kimi Code",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "Goodbye! ✨",
            "response_label": " ✨ Kimi ",
            "prompt_symbol": "✨ ",
            "help_header": "(^_^)? Available Commands",
        },
        "tool_prefix": "│",
    },
    "gurbridge": {
        "name": "gurbridge",
        "description": "Gurbridge IDE — teal grid, electric cyan, amber accents",
        "colors": {
            "banner_border": "#00B8C4",
            "banner_title": "#7DEAFC",
            "banner_accent": "#00E5FF",
            "banner_dim": "#0E5C66",
            "banner_text": "#E0F7FA",
            "ui_accent": "#00E5FF",
            "ui_label": "#7DEAFC",
            "ui_ok": "#7BC96F",
            "ui_error": "#FF6B6B",
            "ui_warn": "#FFC857",
            "prompt": "#E0F7FA",
            "input_rule": "#00B8C4",
            "response_border": "#00E5FF",
            "status_bar_bg": "#0A1A1F",
            "status_bar_text": "#E0F7FA",
            "status_bar_strong": "#7DEAFC",
            "status_bar_dim": "#0E5C66",
            "status_bar_good": "#7BC96F",
            "status_bar_warn": "#FFC857",
            "status_bar_bad": "#FF6B6B",
            "status_bar_critical": "#FF3B5C",
            "session_label": "#7DEAFC",
            "session_border": "#0E5C66",
        },
        "spinner": {
            "waiting_faces": ["(◇)", "(◈)", "(▣)", "(⌬)", "(◊)"],
            "thinking_faces": ["(◇)", "(◈)", "(▣)", "(⌬)", "(╳)"],
            "thinking_verbs": [
                "spanning the gap",
                "routing packets",
                "syncing nodes",
                "linking modules",
                "bridging the loop",
                "channeling agents",
                "wiring threads",
                "lighting up the grid",
            ],
        },
        "branding": {
            "agent_name": "Gurbridge (Kimi)",
            "welcome": "Welcome to Kimi — running inside Gurbridge.",
            "goodbye": "Bridge closed. ⌬",
            "response_label": " ⌬ Kimi/Gurbridge ",
            "prompt_symbol": "⌬ ❯ ",
            "help_header": "(⌬) Available Commands",
        },
        "tool_prefix": "│",
        "banner_logo": """[bold #00E5FF]████████╗██╗  ██╗ █████╗ ███╗   ██╗██╗  ██╗    ███╗   ███╗ ██████╗ ██████╗ ██████╗ ██╗   ██╗██╗      █████╗ ████████╗██╗ ██████╗ ███╗   ██╗[/]
[#00B8C4]██╔══██╗██║  ██║██╔══██╗████╗  ██║██║ ██╔╝    ████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██║   ██║██║     ██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║[/]
[#0E5C66]██████╔╝███████║███████║██╔██╗ ██║█████╔╝     ██╔████╔██║██║   ██║██████╔╝██████╔╝██║   ██║██║     ███████║   ██║   ██║██║   ██║██╔██╗ ██║[/]
[#7DEAFC]██╔══██╗██╔══██║██╔══██║██║╚██╗██║██╔═██╗     ██║╚██╔╝██║██║   ██║██╔══██╗██╔══██╗██║   ██║██║     ██╔══██║   ██║   ██║██║   ██║██║╚██╗██║[/]
[#00E5FF]██║  ██║██║  ██║██║  ██║██║ ╚████║██║  ██╗    ██║ ╚═╝ ██║╚██████╔╝██║  ██║██║  ██║╚██████╔╝███████╗██║  ██║   ██║   ██║██║   ██║██║ ╚████║[/]
[#0E5C66]╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝   ╚═╝╚═╝  ╚═══╝[/]""",
        "banner_hero": """[#00B8C4]                                                         [/]
[#7DEAFC]        ⌬                                      [/]
[#00E5FF]       ╱█╲  Kimi inside Gurbridge               [/]
[#0E5C66]      ╱███╲                                     [/]
[#7DEAFC]     ╱█████╲                                    [/]
[#00E5FF]    ╱███████╲  ─── Bridging Agents ───         [/]
[#0E5C66]   ╱█████████╲                                   [/]
[#7DEAFC]  ╱░░░░░░░░░░╲                                  [/]
[#00E5FF]  ▓▓▓▓▓▓▓▓▓▓▓▓                                  [/]
[#0E5C66]        ║                                       [/]
[#7DEAFC]        ║   Hermes · Kimi · Pi                  [/]
[#00E5FF]       ⌬⌬⌬                                      [/]""",
    },
    "sisyphus": {
        "name": "sisyphus",
        "description": "Sisyphean theme — austere grayscale with persistence",
        "colors": {
            "banner_border": "#B7B7B7",
            "banner_title": "#F5F5F5",
            "banner_accent": "#E7E7E7",
            "banner_dim": "#4A4A4A",
            "banner_text": "#D3D3D3",
            "ui_accent": "#E7E7E7",
            "ui_label": "#D3D3D3",
            "ui_ok": "#919191",
            "ui_error": "#E7E7E7",
            "ui_warn": "#B7B7B7",
            "prompt": "#F5F5F5",
            "input_rule": "#656565",
            "response_border": "#B7B7B7",
            "status_bar_bg": "#202020",
            "status_bar_text": "#D3D3D3",
            "status_bar_strong": "#F5F5F5",
            "status_bar_dim": "#656565",
            "status_bar_good": "#B7B7B7",
            "status_bar_warn": "#D3D3D3",
            "status_bar_bad": "#E7E7E7",
            "status_bar_critical": "#F5F5F5",
            "session_label": "#919191",
            "session_border": "#656565",
        },
        "spinner": {
            "waiting_faces": ["(◉)", "(◌)", "(◬)", "(⬤)", "(::)"],
            "thinking_faces": ["(◉)", "(◬)", "(◌)", "(○)", "(●)"],
            "thinking_verbs": [
                "finding traction",
                "measuring the grade",
                "resetting the boulder",
                "counting the ascent",
                "testing leverage",
                "setting the shoulder",
                "pushing uphill",
                "enduring the loop",
            ],
            "wings": [
                ["⟪◉", "◉⟫"],
                ["⟪◬", "◬⟫"],
                ["⟪◌", "◌⟫"],
                ["⟪⬤", "⬤⟫"],
            ],
        },
        "branding": {
            "agent_name": "Sisyphus Kimi",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "The boulder waits. ◉",
            "response_label": " ◉ Kimi ",
            "prompt_symbol": "◉ ❯ ",
            "help_header": "(◉) Available Commands",
        },
        "tool_prefix": "│",
        "banner_logo": """[bold #F5F5F5]███████╗██╗███████╗██╗   ██╗██████╗ ██╗  ██╗██╗   ██╗███████╗       █████╗  ██████╗ ███████╗███╗   ██╗████████╗[/]
[bold #E7E7E7]██╔════╝██║██╔════╝╚██╗ ██╔╝██╔══██╗██║  ██║██║   ██║██╔════╝      ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/]
[#D7D7D7]███████╗██║███████╗ ╚████╔╝ ██████╔╝███████║██║   ██║███████╗█████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║[/]
[#BFBFBF]╚════██║██║╚════██║  ╚██╔╝  ██╔═══╝ ██╔══██║██║   ██║╚════██║╚════╝██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║[/]
[#8F8F8F]███████║██║███████║   ██║   ██║     ██║  ██║╚██████╔╝███████║      ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║[/]
[#626262]╚══════╝╚═╝╚══════╝   ╚═╝   ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝      ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]""",
        "banner_hero": """[#B7B7B7]                                  [/]
[#D3D3D3]    ⣀⣤⠶⠶⠶⣤⣀                       [/]
[#E7E7E7]   ⣴⠟⠁          ⠙⢿⣆                 [/]
[#F5F5F5]  ⣾⣿⣿⣿⣷                            [/]
[#E7E7E7]  ⣿⣿⣿⣿⣿⣿                            [/]
[#D3D3D3]  ⠘⠿⣿⣿⠿⠃                            [/]
[#B7B7B7]     ⠈⠉                               [/]
[#919191]    ⣰                                       [/]
[#656565]   ⣰⣿                                       [/]
[#4A4A4A]  ⣰⣿                                       [/]
[#4A4A4A] ⣴⣿⣿⣿                                    [/]
[#656565]━━━━━━━━━━━━━━━━━━━━━━                     [/]
[dim #4A4A4A]       the boulder                      [/]""",
    },
    "ares": {
        "name": "ares",
        "description": "War-god theme — crimson and bronze",
        "colors": {
            "banner_border": "#9F1C1C",
            "banner_title": "#C7A96B",
            "banner_accent": "#DD4A3A",
            "banner_dim": "#6B1717",
            "banner_text": "#F1E6CF",
            "ui_accent": "#DD4A3A",
            "ui_label": "#C7A96B",
            "ui_ok": "#4caf50",
            "ui_error": "#ef5350",
            "ui_warn": "#ffa726",
            "prompt": "#F1E6CF",
            "input_rule": "#9F1C1C",
            "response_border": "#C7A96B",
            "status_bar_bg": "#2A1212",
            "status_bar_text": "#F1E6CF",
            "status_bar_strong": "#C7A96B",
            "status_bar_dim": "#6E584B",
            "status_bar_good": "#7BC96F",
            "status_bar_warn": "#C7A96B",
            "status_bar_bad": "#DD4A3A",
            "status_bar_critical": "#EF5350",
            "session_label": "#C7A96B",
            "session_border": "#6E584B",
        },
        "spinner": {
            "waiting_faces": ["(⚔)", "(⛨)", "(▲)", "(<>)", "(/)"],
            "thinking_faces": ["(⚔)", "(⛨)", "(▲)", "(⌁)", "(<>)"],
            "thinking_verbs": [
                "forging",
                "marching",
                "sizing the field",
                "holding the line",
                "hammering plans",
                "tempering steel",
                "plotting impact",
                "raising the shield",
            ],
            "wings": [
                ["⟪⚔", "⚔⟫"],
                ["⟪▲", "▲⟫"],
                ["⟪╸", "╺⟫"],
                ["⟪⛨", "⛨⟫"],
            ],
        },
        "branding": {
            "agent_name": "Ares Kimi",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "Farewell, warrior! ⚔",
            "response_label": " ⚔ Kimi ",
            "prompt_symbol": "⚔ ❯ ",
            "help_header": "(⚔) Available Commands",
        },
        "tool_prefix": "╎",
        "banner_logo": """[bold #A3261F]██████╗  ██████╗ ███████╗███████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗[/]
[bold #B73122]██╔══██╗██╔═══██╗██╔════╝██╔════╝     ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/]
[#C93C24]██████╔╝██║   ██║███████╗███████╗█████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║[/]
[#D84A28]██╔══██╗██║   ██║╚════██║╚════██║╚════╝██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║[/]
[#E15A2D]██║  ██║██║  ██║███████║███████║     ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║[/]
[#EB6C32]╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]""",
        "banner_hero": """[#9F1C1C]                                   [/]
[#9F1C1C]    ⣤⣤                                [/]
[#C7A96B]   ⣴⣿⠟⠻⣿⣦                          [/]
[#C7A96B]  ⣾⠋   ⠠⣄                           [/]
[#DD4A3A] ⣰⣿⠋   ⣰⣿                           [/]
[#DD4A3A] ⣾⠏   ⣰⣿                             [/]
[#9F1C1C] ⣿⠋   ⠸⣿                             [/]
[#9F1C1C] ⣿   ⚔                                 [/]
[#6B1717] ⢿⣧                                 [/]
[#6B1717] ⠘⢿⣷⣄                              [/]
[#C7A96B]   ⠈⠻⣿⣷⣦                           [/]
[#C7A96B]      ⠉⠛⠿                           [/]
[#DD4A3A]         ⚔                            [/]
[dim #6B1717]    war god online                    [/]""",
    },
    "mono": {
        "name": "mono",
        "description": "Monochrome — clean grayscale",
        "colors": {
            "banner_border": "#555555",
            "banner_title": "#e6edf3",
            "banner_accent": "#aaaaaa",
            "banner_dim": "#444444",
            "banner_text": "#c9d1d9",
            "ui_accent": "#aaaaaa",
            "ui_label": "#888888",
            "ui_ok": "#888888",
            "ui_error": "#cccccc",
            "ui_warn": "#999999",
            "prompt": "#c9d1d9",
            "input_rule": "#444444",
            "response_border": "#aaaaaa",
            "status_bar_bg": "#1F1F1F",
            "status_bar_text": "#C9D1D9",
            "status_bar_strong": "#E6EDF3",
            "status_bar_dim": "#777777",
            "status_bar_good": "#B5B5B5",
            "status_bar_warn": "#AAAAAA",
            "status_bar_bad": "#D0D0D0",
            "status_bar_critical": "#F0F0F0",
            "session_label": "#888888",
            "session_border": "#555555",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Kimi Code",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "Goodbye! ✨",
            "response_label": " ✨ Kimi ",
            "prompt_symbol": "❯ ",
            "help_header": "[?] Available Commands",
        },
        "tool_prefix": "┊",
    },
    "slate": {
        "name": "slate",
        "description": "Cool blue — developer-focused",
        "colors": {
            "banner_border": "#4169e1",
            "banner_title": "#7eb8f6",
            "banner_accent": "#8EA8FF",
            "banner_dim": "#4b5563",
            "banner_text": "#c9d1d9",
            "ui_accent": "#7eb8f6",
            "ui_label": "#8EA8FF",
            "ui_ok": "#63D0A6",
            "ui_error": "#F7A072",
            "ui_warn": "#e6a855",
            "prompt": "#c9d1d9",
            "input_rule": "#4169e1",
            "response_border": "#7eb8f6",
            "status_bar_bg": "#151C2F",
            "status_bar_text": "#C9D1D9",
            "status_bar_strong": "#7EB8F6",
            "status_bar_dim": "#4B5563",
            "status_bar_good": "#63D0A6",
            "status_bar_warn": "#E6A855",
            "status_bar_bad": "#F7A072",
            "status_bar_critical": "#FF7A7A",
            "session_label": "#7eb8f6",
            "session_border": "#4b5563",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Kimi Code",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "Goodbye! ✨",
            "response_label": " ✨ Kimi ",
            "prompt_symbol": "❯ ",
            "help_header": "(^_^)? Available Commands",
        },
        "tool_prefix": "┊",
    },
    "daylight": {
        "name": "daylight",
        "description": "Light theme for bright terminals with dark text and cool blue accents",
        "colors": {
            "banner_border": "#2563EB",
            "banner_title": "#0F172A",
            "banner_accent": "#1D4ED8",
            "banner_dim": "#475569",
            "banner_text": "#111827",
            "ui_accent": "#2563EB",
            "ui_label": "#0F766E",
            "ui_ok": "#15803D",
            "ui_error": "#B91C1C",
            "ui_warn": "#B45309",
            "prompt": "#111827",
            "input_rule": "#93C5FD",
            "response_border": "#2563EB",
            "session_label": "#1D4ED8",
            "session_border": "#64748B",
            "status_bar_bg": "#E5EDF8",
            "status_bar_text": "#111827",
            "status_bar_strong": "#1D4ED8",
            "status_bar_dim": "#64748B",
            "status_bar_good": "#15803D",
            "status_bar_warn": "#B45309",
            "status_bar_bad": "#B91C1C",
            "status_bar_critical": "#DC2626",
        },
        "spinner": {},
        "branding": {
            "agent_name": "Kimi Code",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "Goodbye! ✨",
            "response_label": " ✨ Kimi ",
            "prompt_symbol": "❯ ",
            "help_header": "[?] Available Commands",
        },
        "tool_prefix": "│",
    },
    "charizard": {
        "name": "charizard",
        "description": "Volcanic theme — burnt orange and ember",
        "colors": {
            "banner_border": "#C75B1D",
            "banner_title": "#FFD39A",
            "banner_accent": "#F29C38",
            "banner_dim": "#7A3511",
            "banner_text": "#FFF0D4",
            "ui_accent": "#F29C38",
            "ui_label": "#FFD39A",
            "ui_ok": "#4caf50",
            "ui_error": "#ef5350",
            "ui_warn": "#ffa726",
            "prompt": "#FFF0D4",
            "input_rule": "#C75B1D",
            "response_border": "#F29C38",
            "status_bar_bg": "#2B160E",
            "status_bar_text": "#FFF0D4",
            "status_bar_strong": "#FFD39A",
            "status_bar_dim": "#6C4724",
            "status_bar_good": "#6BCB77",
            "status_bar_warn": "#F29C38",
            "status_bar_bad": "#E2832B",
            "status_bar_critical": "#EF5350",
            "session_label": "#FFD39A",
            "session_border": "#6C4724",
        },
        "spinner": {
            "waiting_faces": ["(✦)", "(▲)", "(◇)", "(<>)", "(🔥)"],
            "thinking_faces": ["(✦)", "(▲)", "(◇)", "(⌁)", "(🔥)"],
            "thinking_verbs": [
                "banking into the draft",
                "measuring burn",
                "reading the updraft",
                "tracking ember fall",
                "setting wing angle",
                "holding the flame core",
                "plotting a hot landing",
                "coiling for lift",
            ],
            "wings": [
                ["⟪✦", "✦⟫"],
                ["⟪▲", "▲⟫"],
                ["⟪◌", "◌⟫"],
                ["⟪◇", "◇⟫"],
            ],
        },
        "branding": {
            "agent_name": "Charizard Kimi",
            "welcome": "Welcome to Kimi Code CLI!",
            "goodbye": "Flame out! ✦",
            "response_label": " ✦ Kimi ",
            "prompt_symbol": "✦ ❯ ",
            "help_header": "(✦) Available Commands",
        },
        "tool_prefix": "│",
        "banner_logo": """[bold #FFF0D4]██████╗██╗  ██╗ █████╗ ██████╗ ███████╗ █████╗ ██████╗ ██████╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗[/]
[bold #FFD39A]██╔════╝██║  ██║██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗     ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝[/]
[#F29C38]██║     ███████║███████║██████╔╝███████╗███████║██████╔╝██║  ██║█████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║[/]
[#E2832B]██║     ██╔══██║██╔══██║██╔══██╗╚════██║██╔══██║██╔══██╗██║  ██║╚════╝██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║[/]
[#C75B1D]╚██████╗██║  ██║██║  ██║██║  ██║███████║██║  ██║██║  ██║██████╔╝     ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║[/]
[#7A3511]╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝      ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝[/]""",
        "banner_hero": """[#FFD39A]                               [/]
[#F29C38]   ⣀⣤⠶⠶⠶⣤⣀                      [/]
[#F29C38]  ⣴⠟⠁        ⠙⢿⣦                   [/]
[#E2832B] ⣾⠏   ✦          ⠹⣧                  [/]
[#E2832B] ⣴⠞   ⣀⣤⣤⣤⣀      ⠈⠳⣄              [/]
[#C75B1D] ⣾⠁  ⣰⣿⠟⠉     ⠈⠻⣷⣄  ⠈⠛⢷⣄          [/]
[#C75B1D] ⣿⠃  ⣿⠟             ⠈⠻⣧   ⠻⣧        [/]
[#7A3511]  ⠻⣦                    ⣴⠟          [/]
[#7A3511]    ⠙⢷⣦                          [/]
[#C75B1D]       ⠈⠙⠛⠶⠤                    [/]
[#F29C38]        ⣰                            [/]
[#F29C38]       ⣾                             [/]
[dim #7A3511]    tail flame lit                   [/]""",
    },
}


# =============================================================================
# Skin loading and management
# =============================================================================

_active_skin: Optional[SkinConfig] = None
_active_skin_name: str = "default"


def _skins_dir() -> Path:
    """User skins directory (~/.kimi/skins/)."""
    import os

    home = os.path.expanduser("~")
    return Path(home) / ".kimi" / "skins"


def _load_skin_from_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Load a skin definition from a YAML file."""
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "name" in data:
            return data
    except Exception as e:
        logger.debug("Failed to load skin from %s: %s", path, e)
    return None


def _build_skin_config(data: Dict[str, Any]) -> SkinConfig:
    """Build a SkinConfig from a raw dict (built-in or loaded from YAML)."""
    # Start with default values as base for missing keys
    default = _BUILTIN_SKINS.get("default", {})
    colors = dict(default.get("colors", {}))
    colors.update(data.get("colors", {}))
    spinner = dict(default.get("spinner", {}))
    spinner.update(data.get("spinner", {}))
    branding = dict(default.get("branding", {}))
    branding.update(data.get("branding", {}))

    return SkinConfig(
        name=data.get("name", "unknown"),
        description=data.get("description", ""),
        colors=colors,
        spinner=spinner,
        branding=branding,
        tool_prefix=data.get("tool_prefix", default.get("tool_prefix", "│")),
        tool_emojis=data.get("tool_emojis", {}),
        banner_logo=data.get("banner_logo", ""),
        banner_hero=data.get("banner_hero", ""),
    )


def list_skins() -> List[Dict[str, str]]:
    """List all available skins (built-in + user-installed).

    Returns list of {"name": ..., "description": ..., "source": "builtin"|"user"}.
    """
    result = []
    for name, data in _BUILTIN_SKINS.items():
        result.append({
            "name": name,
            "description": data.get("description", ""),
            "source": "builtin",
        })

    skins_path = _skins_dir()
    if skins_path.is_dir():
        for f in sorted(skins_path.glob("*.yaml")):
            data = _load_skin_from_yaml(f)
            if data:
                skin_name = data.get("name", f.stem)
                # Skip if it shadows a built-in
                if any(s["name"] == skin_name for s in result):
                    continue
                result.append({
                    "name": skin_name,
                    "description": data.get("description", ""),
                    "source": "user",
                })

    return result


def load_skin(name: str) -> SkinConfig:
    """Load a skin by name. Checks user skins first, then built-in."""
    # Check user skins directory
    skins_path = _skins_dir()
    user_file = skins_path / f"{name}.yaml"
    if user_file.is_file():
        data = _load_skin_from_yaml(user_file)
        if data:
            return _build_skin_config(data)

    # Check built-in skins
    if name in _BUILTIN_SKINS:
        return _build_skin_config(_BUILTIN_SKINS[name])

    # Fallback to default
    logger.warning("Skin '%s' not found, using default", name)
    return _build_skin_config(_BUILTIN_SKINS["default"])


def get_active_skin() -> SkinConfig:
    """Get the currently active skin config (cached).

    Reads GURBRIDGE_SKIN env var first, then KIMI_SKIN, falling back to "default".
    """
    global _active_skin, _active_skin_name

    if _active_skin is None:
        # Priority: GURBRIDGE_SKIN > KIMI_SKIN > default
        skin_name = os.environ.get("GURBRIDGE_SKIN") or os.environ.get("KIMI_SKIN", "default")
        _active_skin_name = skin_name
        _active_skin = load_skin(skin_name)

    return _active_skin


def set_active_skin(name: str) -> SkinConfig:
    """Switch the active skin. Returns the new SkinConfig."""
    global _active_skin, _active_skin_name
    _active_skin_name = name
    _active_skin = load_skin(name)
    return _active_skin


def get_active_skin_name() -> str:
    """Get the name of the currently active skin."""
    return _active_skin_name


def init_skin_from_config(config: dict) -> None:
    """Initialize the active skin from CLI config at startup.

    Call this once during CLI init with the loaded config dict.
    Checks GURBRIDGE_SKIN and KIMI_SKIN env vars first.
    """
    # Env vars take precedence over config
    env_skin = os.environ.get("GURBRIDGE_SKIN") or os.environ.get("KIMI_SKIN")
    if env_skin:
        set_active_skin(env_skin)
        return

    display = config.get("display") or {}
    if not isinstance(display, dict):
        display = {}
    skin_name = display.get("skin", "default")
    if isinstance(skin_name, str) and skin_name.strip():
        set_active_skin(skin_name.strip())
    else:
        set_active_skin("default")


# =============================================================================
# Convenience helpers
# =============================================================================


def get_active_prompt_symbol(fallback: str = "✨ ") -> str:
    """Get the interactive prompt symbol from the active skin."""
    try:
        return get_active_skin().get_branding("prompt_symbol", fallback)
    except Exception:
        return fallback


def get_active_help_header(fallback: str = "(^_^)? Available Commands") -> str:
    """Get the /help header from the active skin."""
    try:
        return get_active_skin().get_branding("help_header", fallback)
    except Exception:
        return fallback


def get_active_goodbye(fallback: str = "Goodbye! ✨") -> str:
    """Get the goodbye line from the active skin."""
    try:
        return get_active_skin().get_branding("goodbye", fallback)
    except Exception:
        return fallback


def get_active_welcome(fallback: str = "Welcome to Kimi Code CLI!") -> str:
    """Get the welcome message from the active skin."""
    try:
        return get_active_skin().get_branding("welcome", fallback)
    except Exception:
        return fallback


def get_active_banner_logo() -> str:
    """Get the banner logo from the active skin (Rich markup)."""
    try:
        return get_active_skin().banner_logo
    except Exception:
        return ""


def get_active_ui_accent() -> str:
    """Get the ui_accent color from the active skin."""
    try:
        return get_active_skin().get_color("ui_accent", "#FFBF00")
    except Exception:
        return "#FFBF00"


# Expose BUILTIN_SKINS for external use
BUILTIN_SKINS = _BUILTIN_SKINS
