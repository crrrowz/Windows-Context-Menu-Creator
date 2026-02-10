"""
Pre-built MenuEntry presets for common applications.
Import and use directly, or use as templates for custom entries.
"""

from config import MenuEntry, TargetScope

# ── Sublime Text ────────────────────────────────────────────────
SUBLIME_FILES = MenuEntry(
    key_name="SublimeText",
    display_name="Edit with Sublime Text",
    exe_path=r"C:\Program Files\Sublime Text\sublime_text.exe",
    icon=r"C:\Program Files\Sublime Text\sublime_text.exe,0",
    scopes=[TargetScope.ALL_FILES],
)

SUBLIME_FOLDERS = MenuEntry(
    key_name="SublimeTextDir",
    display_name="Open Folder in Sublime Text",
    exe_path=r"C:\Program Files\Sublime Text\sublime_text.exe",
    icon=r"C:\Program Files\Sublime Text\sublime_text.exe,0",
    scopes=[TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND],
)

# ── VS Code ─────────────────────────────────────────────────────
VSCODE_FILES = MenuEntry(
    key_name="VSCode",
    display_name="Open with VS Code",
    exe_path=r"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    icon=r"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe,0",
    scopes=[TargetScope.ALL_FILES],
)

VSCODE_FOLDERS = MenuEntry(
    key_name="VSCodeDir",
    display_name="Open Folder in VS Code",
    exe_path=r"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    icon=r"C:\Users\{USERNAME}\AppData\Local\Programs\Microsoft VS Code\Code.exe,0",
    scopes=[TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND],
)

# ── Notepad++ (extension-specific) ──────────────────────────────
NOTEPADPP_CODE = MenuEntry(
    key_name="NotepadPP",
    display_name="Edit with Notepad++",
    exe_path=r"C:\Program Files\Notepad++\notepad++.exe",
    icon=r"C:\Program Files\Notepad++\notepad++.exe,0",
    scopes=[TargetScope.EXTENSION],
    extensions=[".txt", ".py", ".js", ".json", ".xml", ".html", ".css", ".md"],
)

# ── Windows Terminal (directory) ────────────────────────────────
TERMINAL_HERE = MenuEntry(
    key_name="TerminalHere",
    display_name="Open Terminal Here",
    exe_path=r"C:\Users\{USERNAME}\AppData\Local\Microsoft\WindowsApps\wt.exe",
    command_template='"{exe_path}" -d "{target}"',
    icon=r"C:\Users\{USERNAME}\AppData\Local\Microsoft\WindowsApps\wt.exe,0",
    scopes=[TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND],
)
