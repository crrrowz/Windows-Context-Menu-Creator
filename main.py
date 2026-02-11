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


def _pick_exe_file() -> str | None:
    """Open a native Windows file dialog to select an .exe file."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()          # Hide the empty tkinter window
    root.attributes("-topmost", True)  # Dialog appears on top
    path = filedialog.askopenfilename(
        title="Select Application (.exe)",
        filetypes=[("Executables", "*.exe"), ("All Files", "*.*")],
    )
    root.destroy()
    return path or None


def _derive_app_name(exe_path: str) -> str:
    """
    Derive a clean app name from the exe filename.
    'sublime_text.exe' → 'Sublime Text'
    'Code.exe'         → 'Code'
    """
    from pathlib import Path
    stem = Path(exe_path).stem                    # 'sublime_text'
    return stem.replace("_", " ").replace("-", " ").title()


def _build_custom_entry() -> MenuEntry:
    """
    Interactive prompt to build a MenuEntry from user input.
    Auto-opens Explorer to pick the .exe, then derives key_name,
    display_name, and icon automatically.
    """
    print("\n╔══════════════════════════════════════════╗")
    print("║   Windows Context Menu Creator — Setup   ║")
    print("╚══════════════════════════════════════════╝\n")

    # ── Step 1: Pick the executable ─────────────────────────────
    print("  Press Enter to open file picker, or paste a path directly.")
    manual = input("  Full path to .exe: ").strip()
    if manual:
        exe_path = manual
    else:
        exe_path = _pick_exe_file()
        if not exe_path:
            print("  ✗ No file selected. Aborting.")
            sys.exit(1)
        print(f"  ✔ Selected: {exe_path}")

    # ── Step 2: Auto-derive names ───────────────────────────────
    app_name = _derive_app_name(exe_path)
    default_key = app_name.replace(" ", "")           # "SublimeText"
    default_display = f"Open with {app_name}"         # "Open with Sublime Text"
    default_icon = f"{exe_path},0"                    # Use the exe's first icon

    key_name = input(f"  Registry key name [{default_key}]: ").strip() or default_key
    display_name = input(f"  Display label [{default_display}]: ").strip() or default_display
    icon_input = input(f"  Icon path [{default_icon}]: ").strip()
    icon = icon_input if icon_input else default_icon

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


def _interactive_remove(manager: RegistryManager) -> None:
    """
    Show all existing context-menu entries with numbered IDs,
    then let the user pick by number to remove.
    """
    # Collect entries from all scopes
    scope_entries: dict[TargetScope, list[str]] = {}
    all_keys: list[str] = []  # ordered, unique

    for scope in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
        entries = manager.list_entries(scope)
        scope_entries[scope] = entries
        for e in entries:
            if e not in all_keys:
                all_keys.append(e)

    if not all_keys:
        print("\n  No context-menu entries found.")
        return

    # Display numbered list with scope tags
    scope_labels = {
        TargetScope.ALL_FILES:      "*",
        TargetScope.DIRECTORY:      "Dir",
        TargetScope.DIR_BACKGROUND: "DirBG",
    }

    print("\n╔══════════════════════════════════════════╗")
    print("║       Existing Context Menu Entries      ║")
    print("╚══════════════════════════════════════════╝\n")

    for idx, key in enumerate(all_keys, 1):
        # Show which scopes this key exists in
        tags = [
            label for scope, label in scope_labels.items()
            if key in scope_entries.get(scope, [])
        ]
        tag_str = ", ".join(tags)
        print(f"  {idx:3d} │ {key:<35s} [{tag_str}]")

    # Ask for the number
    print()
    choice = input("  Enter number to remove (or 'q' to cancel): ").strip()
    if choice.lower() == "q" or not choice:
        print("  Cancelled.")
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(all_keys):
            raise ValueError
    except ValueError:
        print(f"  ✗ Invalid selection: '{choice}'")
        return

    key_name = all_keys[idx]

    # Confirm
    confirm = input(f"  Remove '{key_name}' from all scopes? [y/N]: ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return

    # Find which scopes contain this key and remove from all of them
    target_scopes = [s for s, entries in scope_entries.items() if key_name in entries]

    from config import MenuEntry
    entry = MenuEntry(
        key_name=key_name,
        display_name="",
        exe_path="C:\\dummy.exe",
        scopes=target_scopes,
    )
    manager.remove_entry(entry)


def _list_entries(manager: RegistryManager) -> None:
    """Display all existing shell entries grouped by scope."""
    scope_labels = {
        TargetScope.ALL_FILES:      "All Files (*)",
        TargetScope.DIRECTORY:      "Directory",
        TargetScope.DIR_BACKGROUND: r"Directory\Background",
    }

    found = False
    for scope, label in scope_labels.items():
        entries = manager.list_entries(scope)
        if entries:
            found = True
            print(f"\n  ── {label} ──")
            for name in entries:
                print(f"     • {name}")

    if not found:
        print("\n  No context-menu entries found.")


def _interactive_edit(manager: RegistryManager) -> None:
    """
    Pick an existing entry, show its current details,
    then let the user change the target scopes.
    """
    # Collect all entries
    scope_entries: dict[TargetScope, list[str]] = {}
    all_keys: list[str] = []

    scope_labels_short = {
        TargetScope.ALL_FILES:      "*",
        TargetScope.DIRECTORY:      "Dir",
        TargetScope.DIR_BACKGROUND: "DirBG",
    }

    for scope in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
        entries = manager.list_entries(scope)
        scope_entries[scope] = entries
        for e in entries:
            if e not in all_keys:
                all_keys.append(e)

    if not all_keys:
        print("\n  No context-menu entries found.")
        return

    print("\n╔══════════════════════════════════════════╗")
    print("║         Select Entry to Edit             ║")
    print("╚══════════════════════════════════════════╝\n")

    for idx, key in enumerate(all_keys, 1):
        tags = [lbl for s, lbl in scope_labels_short.items() if key in scope_entries.get(s, [])]
        print(f"  {idx:3d} │ {key:<35s} [{', '.join(tags)}]")

    print()
    choice = input("  Enter number to edit (or 'q' to cancel): ").strip()
    if choice.lower() == "q" or not choice:
        print("  Cancelled.")
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(all_keys):
            raise ValueError
    except ValueError:
        print(f"  ✗ Invalid selection: '{choice}'")
        return

    key_name = all_keys[idx]
    current_scopes = [s for s, entries in scope_entries.items() if key_name in entries]

    # Read details from the first scope it exists in
    details = manager.read_entry_details(current_scopes[0], key_name)
    if not details:
        print(f"  ✗ Could not read details for '{key_name}'.")
        return

    # Show current details
    cur_tags = [scope_labels_short[s] for s in current_scopes]
    print(f"\n  ── Current Config for '{key_name}' ──")
    print(f"     Display : {details['display_name']}")
    print(f"     Icon    : {details['icon'] or '(none)'}")
    print(f"     Command : {details['command']}")
    print(f"     Scopes  : {', '.join(cur_tags)}")

    # Ask for new scopes
    print("\n  New target scopes:")
    print("    1 → All files  (*)")
    print("    2 → Directories")
    print("    3 → Directory background")
    print("    4 → Specific extensions")
    scope_input = input("  Choose new scopes (comma-separated, e.g. 4): ").strip()

    scope_map = {
        "1": TargetScope.ALL_FILES,
        "2": TargetScope.DIRECTORY,
        "3": TargetScope.DIR_BACKGROUND,
        "4": TargetScope.EXTENSION,
    }
    new_scopes = [scope_map[s.strip()] for s in scope_input.split(",") if s.strip() in scope_map]

    if not new_scopes:
        print("  ✗ No valid scopes selected.")
        return

    extensions: list[str] = []
    if TargetScope.EXTENSION in new_scopes:
        ext_input = input("  Extensions (comma-separated, e.g. .py,.js,.html): ").strip()
        extensions = [e.strip() for e in ext_input.split(",") if e.strip()]
        if not extensions:
            print("  ✗ No extensions provided.")
            return

    # Extract exe_path from the existing command (between first pair of quotes)
    cmd = details["command"] or ""
    if cmd.startswith('"'):
        exe_path = cmd.split('"')[1]
    else:
        exe_path = cmd.split()[0] if cmd else ""

    # Step 1: Remove from ALL old scopes
    from config import MenuEntry
    old_entry = MenuEntry(
        key_name=key_name,
        display_name=details["display_name"],
        exe_path=exe_path or "C:\\dummy.exe",
        scopes=current_scopes,
    )
    manager.remove_entry(old_entry)

    # Step 2: Re-add with new scopes
    new_entry = MenuEntry(
        key_name=key_name,
        display_name=details["display_name"],
        exe_path=exe_path,
        icon=details["icon"],
        scopes=new_scopes,
        extensions=extensions,
    )
    manager.add_entry(new_entry)

    new_tags = [scope_labels_short.get(s, "Ext") for s in new_scopes]
    if extensions:
        print(f"\n  ✔ '{key_name}' updated: [{', '.join(cur_tags)}] → [{', '.join(new_tags)}] ({', '.join(extensions)})")
    else:
        print(f"\n  ✔ '{key_name}' updated: [{', '.join(cur_tags)}] → [{', '.join(new_tags)}]")


def main() -> None:
    manager_ro = RegistryManager(dry_run=False)
    is_classic = manager_ro.is_classic_menu_forced()
    status_icon = "🟢 ON" if is_classic else "🔴 OFF"

    print("\n╔══════════════════════════════════════════╗")
    print("║   Windows Context Menu Creator  v1.0     ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print("  1 → Add new entry")
    print("  2 → Remove an entry")
    print("  3 → List existing entries")
    print("  4 → Edit an entry (change scopes)")
    print(f"  5 → Toggle Win11 Classic Menu [{status_icon}]")
    print("  6 → Exit")
    print()

    choice = input("  Choose an option [1-6]: ").strip()

    try:
        if choice == "1":
            manager = RegistryManager(dry_run=False)
            entry = _build_custom_entry()
            manager.add_entry(entry)

        elif choice == "2":
            manager = RegistryManager(dry_run=False)
            _interactive_remove(manager)

        elif choice == "3":
            manager = RegistryManager(dry_run=False)
            _list_entries(manager)

        elif choice == "4":
            manager = RegistryManager(dry_run=False)
            _interactive_edit(manager)

        elif choice == "5":
            manager = RegistryManager(dry_run=False)
            if is_classic:
                print("\n  Restoring modern Win11 compact menu…")
                manager.restore_modern_menu()
            else:
                print("\n  Forcing classic full menu (Win10 style)…")
                manager.force_classic_menu()

            restart = input("  Restart Explorer now to apply? [y/N]: ").strip().lower()
            if restart == "y":
                manager.restart_explorer()
                print("  ✔ Done! Right-click to see the change.")
            else:
                print("  ⚠ Change saved. Restart Explorer manually or reboot to apply.")

        elif choice == "6":
            print("  Bye!")

        else:
            print(f"  ✗ Invalid option: '{choice}'")
            sys.exit(1)

    except PermissionError:
        print("\n  ✗ This operation requires Administrator privileges.")
        print("    Right-click your terminal → 'Run as administrator'.")
        sys.exit(1)


if __name__ == "__main__":
    if "--gui" in sys.argv:
        from gui import launch
        launch()
    elif "--browser" in sys.argv:
        from server import start_gui
        start_gui()
    else:
        main()
