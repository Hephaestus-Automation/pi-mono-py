"""
pi-tui: Terminal UI library with differential rendering

Python port of @mariozechner/pi-tui from the pi-mono monorepo.

TypeScript Reference: _ts_reference/tui.ts, _ts_reference/index.ts
"""

from pi_tui.component import Component, Focusable, is_focusable
from pi_tui.components import (
    Box,
    CancellableLoader,
    DefaultSelectListTheme,
    Input,
    Loader,
    SelectItem,
    SelectList,
    Spacer,
    Text,
    TruncatedText,
)
from pi_tui.container import Container
from pi_tui.keys import (
    Key,
    KeyEventType,
    KeyId,
    is_key_release,
    is_key_repeat,
    matches_key,
    parse_key,
)
from pi_tui.stdin_buffer import StdinBuffer, StdinBufferOptions
from pi_tui.terminal import ProcessTerminal, Terminal
from pi_tui.tui import (
    CURSOR_MARKER,
    TUI,
    OverlayAnchor,
    OverlayHandle,
    OverlayMargin,
    OverlayOptions,
    SizeValue,
)
from pi_tui.utils import (
    truncate_to_width,
    visible_width,
    wrap_text_with_ansi,
)

__all__ = [
    "Component",
    "Focusable",
    "is_focusable",
    "Container",
    "TUI",
    "CURSOR_MARKER",
    "Terminal",
    "ProcessTerminal",
    "Key",
    "KeyId",
    "KeyEventType",
    "parse_key",
    "matches_key",
    "is_key_release",
    "is_key_repeat",
    "StdinBuffer",
    "StdinBufferOptions",
    "visible_width",
    "truncate_to_width",
    "wrap_text_with_ansi",
    "OverlayAnchor",
    "OverlayHandle",
    "OverlayMargin",
    "OverlayOptions",
    "SizeValue",
    "Text",
    "Box",
    "TruncatedText",
    "Spacer",
    "Loader",
    "CancellableLoader",
    "Input",
    "SelectList",
    "SelectItem",
    "DefaultSelectListTheme",
]
