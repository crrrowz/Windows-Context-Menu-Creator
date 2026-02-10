"""
CLI entry point for the Windows Context Menu Creator.

Usage (run as Administrator):
    python main.py add      — Register entries
    python main.py remove   — Unregister entries
    python main.py list     — Show existing shell entries
    python main.py dry-add  — Simulate registration (no writes)
"""

from __future__ import annotations

import sys

from config import MenuEntry, TargetScope
from registry_manager import RegistryManager
from safety import require_admin
from logger_setup import get_logger

log = get_logger("main")


def _build_custom_entry() -> MenuEntry:
    """
    Interactive prompt to build a MenuEntry from user input.
    Replace this with your own entries or import from examples.py.
    """
    print("\n╔══════════════════════════════════════════╗")
    print("║   Windows Context Menu Creator — Setup   ║")
    print("╚══════════════════════════════════════════╝\n")

    key_name = input("  Registry key name (no spaces, e.g. SublimeText): ").strip()
    display_name = input("  Display label (e.g. 'Edit with Sublime Text'): ").strip()
    exe_path = input("  Full path to .exe: ").strip()
    icon = input("  Icon path (leave blank to skip): ").strip() or None

    print("\n  Target scopes:")
    print("    1 → All files  (*)          ")
    print("    2 → Directories             ")
    print("    3 → Directory background    ")
    print("    4 → Specific extensions     ")
    scope_input = input("  Choose scopes (comma-separated, e.g. 1,2): ").strip()

    scope_map = {
        "1": TargetScope.ALL_FILES,
        "2": TargetScope.DIRECTORY,
        "3": TargetScope.DIR_BACKGROUND,
        "4": TargetScope.EXTENSION,
    }
    scopes = [scope_map[s.strip()] for s in scope_input.split(",") if s.strip() in scope_map]

    extensions: list[str] = []
    if TargetScope.EXTENSION in scopes:
        ext_input = input("  Extensions (comma-separated, e.g. .txt,.py): ").strip()
        extensions = [e.strip() for e in ext_input.split(",") if e.strip()]

    cmd_template = input(
        '  Command template (default: "{exe_path}" "{target}"): '
    ).strip()
    if not cmd_template:
        cmd_template = '"{exe_path}" "{target}"'

    return MenuEntry(
        key_name=key_name,
        display_name=display_name,
        exe_path=exe_path,
        icon=icon,
        scopes=scopes,
        extensions=extensions,
        command_template=cmd_template,
    )


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1].lower()
    dry_run = action.startswith("dry-")
    action = action.replace("dry-", "") if dry_run else action

    manager = RegistryManager(dry_run=dry_run)

    if action == "add":
        entry = _build_custom_entry()
        manager.add_entry(entry)

    elif action == "remove":
        entry = _build_custom_entry()
        manager.remove_entry(entry)

    elif action == "list":
        print("\n── Entries under * (all files) ──")
        for name in manager.list_entries(TargetScope.ALL_FILES):
            print(f"   • {name}")

        print("\n── Entries under Directory ──")
        for name in manager.list_entries(TargetScope.DIRECTORY):
            print(f"   • {name}")

        print("\n── Entries under Directory\\Background ──")
        for name in manager.list_entries(TargetScope.DIR_BACKGROUND):
            print(f"   • {name}")

        ext = input("\nCheck a specific extension? (e.g. .txt, or blank to skip): ").strip()
        if ext:
            print(f"\n── Entries under {ext} ──")
            for name in manager.list_entries(TargetScope.EXTENSION, extension=ext):
                print(f"   • {name}")

    else:
        print(f"Unknown action: '{action}'. Use add | remove | list | dry-add | dry-remove")
        sys.exit(1)


if __name__ == "__main__":
    main()
