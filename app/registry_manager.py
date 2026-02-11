"""
Registry Manager — the ONLY module that touches winreg.

All operations route through `add_entry` / `remove_entry`.
Dry-run mode logs what WOULD happen without writing.
"""

from __future__ import annotations

import winreg
from typing import Optional

from app.config import MenuEntry, TargetScope
from app.safety import require_admin, validate_exe_path, validate_icon_path
from app.logger_setup import get_logger

log = get_logger("registry")

# ── Scope → Registry root path mapping ─────────────────────────
_SCOPE_ROOTS: dict[TargetScope, str] = {
    TargetScope.ALL_FILES:      r"*\shell",
    TargetScope.DIRECTORY:      r"Directory\shell",
    TargetScope.DIR_BACKGROUND: r"Directory\Background\shell",
    # EXTENSION is dynamic — handled separately
}

# %1 = selected file path, %V = current directory path
_SCOPE_PLACEHOLDER: dict[TargetScope, str] = {
    TargetScope.ALL_FILES:      "%1",
    TargetScope.DIRECTORY:      "%V",
    TargetScope.DIR_BACKGROUND: "%V",
    TargetScope.EXTENSION:      "%1",
}


class RegistryManager:
    """
    High-level API for context-menu registry operations.

    Parameters
    ----------
    dry_run : bool
        If True, every operation is logged but NO registry writes occur.
    """

    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        if dry_run:
            log.info("══════ DRY-RUN MODE — no registry changes will be made ══════")

    # ── Public API ──────────────────────────────────────────────

    def add_entry(self, entry: MenuEntry) -> None:
        """Register a context-menu entry across all requested scopes."""
        require_admin()
        exe = validate_exe_path(entry.exe_path)
        icon = validate_icon_path(entry.icon)

        for scope in entry.scopes:
            if scope == TargetScope.EXTENSION:
                for ext in entry.extensions:
                    root = rf"{ext}\shell"
                    self._write_entry(root, entry, _SCOPE_PLACEHOLDER[scope], icon)
            else:
                root = _SCOPE_ROOTS[scope]
                self._write_entry(root, entry, _SCOPE_PLACEHOLDER[scope], icon)

        log.info("✔ Entry '%s' registered successfully.", entry.key_name)

    def remove_entry(self, entry: MenuEntry) -> None:
        """Remove a context-menu entry from all its scopes."""
        require_admin()

        for scope in entry.scopes:
            if scope == TargetScope.EXTENSION:
                for ext in entry.extensions:
                    root = rf"{ext}\shell"
                    self._delete_entry(root, entry.key_name)
            else:
                root = _SCOPE_ROOTS[scope]
                self._delete_entry(root, entry.key_name)

        log.info("✔ Entry '%s' removed successfully.", entry.key_name)

    def list_entries(self, scope: TargetScope, extension: str | None = None) -> list[str]:
        """
        List all custom shell entries under a given scope.
        Returns a list of subkey names.
        """
        if scope == TargetScope.EXTENSION:
            if extension is None:
                raise ValueError("Must provide `extension` for EXTENSION scope.")
            root = rf"{extension}\shell"
        else:
            root = _SCOPE_ROOTS[scope]

        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, root) as key:
                count = winreg.QueryInfoKey(key)[0]  # number of subkeys
                return [winreg.EnumKey(key, i) for i in range(count)]
        except FileNotFoundError:
            return []

    def read_entry_details(self, scope: TargetScope, key_name: str) -> dict | None:
        """
        Read display_name, icon, and command from an existing registry entry.
        Returns a dict or None if not found.
        """
        root = _SCOPE_ROOTS.get(scope)
        if root is None:
            return None

        key_path = rf"{root}\{key_name}"
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                display_name = winreg.QueryValueEx(key, "")[0]
                try:
                    icon = winreg.QueryValueEx(key, "Icon")[0]
                except FileNotFoundError:
                    icon = None
        except FileNotFoundError:
            return None

        cmd_path = rf"{key_path}\command"
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, cmd_path) as key:
                command = winreg.QueryValueEx(key, "")[0]
        except FileNotFoundError:
            command = None

        return {
            "display_name": display_name,
            "icon": icon,
            "command": command,
        }

    # ── Internal helpers ────────────────────────────────────────

    def _write_entry(
        self,
        root: str,
        entry: MenuEntry,
        placeholder: str,
        icon: Optional[str],
    ) -> None:
        r"""Create the shell\<key>\command tree under `root`."""
        key_path = rf"{root}\{entry.key_name}"
        cmd_path = rf"{key_path}\command"
        command = entry.build_command(placeholder)

        if self.dry_run:
            log.info("[DRY-RUN] Would create: HKCR\\%s", key_path)
            log.info("[DRY-RUN]   (Default) = %s", entry.display_name)
            if icon:
                log.info("[DRY-RUN]   Icon     = %s", icon)
            log.info("[DRY-RUN]   command  = %s", command)
            return

        # Create parent key + set display name
        with winreg.CreateKeyEx(
            winreg.HKEY_CLASSES_ROOT, key_path,
            access=winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, entry.display_name)
            if icon:
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)

        # Create command subkey
        with winreg.CreateKeyEx(
            winreg.HKEY_CLASSES_ROOT, cmd_path,
            access=winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

        log.debug("Created: HKCR\\%s → %s", key_path, command)

    def _delete_entry(self, root: str, key_name: str) -> None:
        r"""Delete shell\<key_name> and its command subkey."""
        key_path = rf"{root}\{key_name}"
        cmd_path = rf"{key_path}\command"

        if self.dry_run:
            log.info("[DRY-RUN] Would delete: HKCR\\%s", key_path)
            return

        # Must delete children first (command subkey)
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, cmd_path)
            log.debug("Deleted: HKCR\\%s", cmd_path)
        except FileNotFoundError:
            log.warning("Key not found (skip): HKCR\\%s", cmd_path)

        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            log.debug("Deleted: HKCR\\%s", key_path)
        except FileNotFoundError:
            log.warning("Key not found (skip): HKCR\\%s", key_path)

    # ── Windows 11 Menu Style ──────────────────────────────────

    # This CLSID disables the modern compact menu when its
    # InprocServer32 default value is set to an empty string.
    _WIN11_CLSID = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"

    def is_classic_menu_forced(self) -> bool:
        """Check if Windows 11 is set to always show the classic menu."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self._WIN11_CLSID) as key:
                val, _ = winreg.QueryValueEx(key, "")
                return val == ""
        except (FileNotFoundError, OSError):
            return False

    def force_classic_menu(self) -> None:
        """
        Force Windows 11 to always show the full classic context menu
        instead of the compact modern menu.
        Requires Explorer restart to take effect.
        """
        if self.dry_run:
            log.info("[DRY-RUN] Would force classic menu (disable Win11 compact menu)")
            return

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, self._WIN11_CLSID,
            access=winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "")

        log.info("✔ Classic menu forced. Restart Explorer to apply.")

    def restore_modern_menu(self) -> None:
        """
        Restore the Windows 11 compact/modern context menu.
        Requires Explorer restart to take effect.
        """
        if self.dry_run:
            log.info("[DRY-RUN] Would restore modern Win11 menu")
            return

        try:
            winreg.DeleteKey(
                winreg.HKEY_CURRENT_USER,
                self._WIN11_CLSID,
            )
            # Also clean up parent CLSID key if empty
            parent = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}"
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent)
            except OSError:
                pass
            log.info("✔ Modern menu restored. Restart Explorer to apply.")
        except FileNotFoundError:
            log.info("Modern menu is already active.")

    @staticmethod
    def restart_explorer() -> None:
        """Kill and restart explorer.exe to apply menu changes."""
        import subprocess
        log.info("Restarting Explorer…")
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"],
                       capture_output=True)
        subprocess.Popen(["explorer.exe"])
        log.info("✔ Explorer restarted.")
