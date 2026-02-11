"""
Configuration layer — pure data, zero side-effects.

A `MenuEntry` describes ONE context-menu item.
`TargetScope` controls WHERE in the registry it appears.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TargetScope(Enum):
    """Where the context-menu entry will appear."""

    ALL_FILES = auto()        # HKCR\*\shell
    DIRECTORY = auto()        # HKCR\Directory\shell
    DIR_BACKGROUND = auto()   # HKCR\Directory\Background\shell
    EXTENSION = auto()        # HKCR\.ext\shell  (requires `extensions` list)


@dataclass
class MenuEntry:
    """
    Immutable description of a single context-menu registration.

    Parameters
    ----------
    key_name : str
        Internal registry key name (no spaces, e.g. "SublimeText").
    display_name : str
        Label shown to the user in Explorer.
    exe_path : str
        Absolute path to the executable.
    command_template : str
        Template string.  Use ``{exe_path}`` and ``{target}`` as placeholders.
        Default:  '"{exe_path}" "{target}"'
    icon : str | None
        Path to the icon. Can include index: "app.exe,0".
    scopes : list[TargetScope]
        Where the entry should be registered.
    extensions : list[str]
        Required when TargetScope.EXTENSION is in `scopes`.
        Each entry should include the leading dot, e.g. [".txt", ".py"].
    """

    key_name: str
    display_name: str
    exe_path: str
    command_template: str = '"{exe_path}" "{target}"'
    icon: Optional[str] = None
    scopes: list[TargetScope] = field(default_factory=lambda: [TargetScope.ALL_FILES])
    extensions: list[str] = field(default_factory=list)

    def build_command(self, placeholder: str = "%1") -> str:
        """Render the final command string for the registry."""
        return self.command_template.format(
            exe_path=self.exe_path.replace("/", "\\"),
            target=placeholder,
        )

    def __post_init__(self) -> None:
        if TargetScope.EXTENSION in self.scopes and not self.extensions:
            raise ValueError(
                f"MenuEntry '{self.key_name}': TargetScope.EXTENSION requires "
                f"a non-empty `extensions` list."
            )
        # Normalize paths: forward → backslashes (Windows Registry requirement)
        self.exe_path = self.exe_path.replace("/", "\\")
        if self.icon:
            self.icon = self.icon.replace("/", "\\")
        # Normalize extensions to include leading dot
        self.extensions = [
            ext if ext.startswith(".") else f".{ext}"
            for ext in self.extensions
        ]
