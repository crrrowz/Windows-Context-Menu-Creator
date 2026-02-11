"""
Lightweight HTTP API server — bridges the Web UI to RegistryManager.

Endpoints:
    GET  /api/entries          → list all entries from all scopes
    GET  /api/entry/<key>      → read details for a specific key
    POST /api/entries          → add a new entry
    DELETE /api/entries/<key>  → remove an entry
    PUT  /api/entries/<key>    → edit (change scopes)
    POST /api/pick-file        → open native file dialog, return path
    GET  /                     → serve static/index.html
"""

from __future__ import annotations

import json
import os
import sys
import threading
import webbrowser
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote

from app.config import MenuEntry, TargetScope
from app.registry_manager import RegistryManager
from app.safety import is_admin
from app.logger_setup import get_logger

log = get_logger("server")

# ── PyInstaller / Nuitka compatible base path ──────────────────
if getattr(sys, 'frozen', False):
    _BASE_DIR = Path(sys._MEIPASS)  # PyInstaller temp folder (static assets)
else:
    _BASE_DIR = Path(__file__).parent.parent  # project root (app/ → root)

# Logs/crash in a fixed user-accessible location
_APP_DIR = Path(os.environ.get("TEMP", r"C:\temp")) / "ContextMenuCreator"

_STATIC_DIR = _BASE_DIR / "static"
_LOG_FILE = _APP_DIR / "logs" / "context_menu.log"
_LOG_BACKUP_DIR = _APP_DIR / "logs" / "backups"
_PORT = 8787

# Scope string ↔ enum mapping
_SCOPE_FROM_STR: dict[str, TargetScope] = {
    "all_files":      TargetScope.ALL_FILES,
    "directory":      TargetScope.DIRECTORY,
    "dir_background": TargetScope.DIR_BACKGROUND,
    "extension":      TargetScope.EXTENSION,
}

_SCOPE_TO_STR: dict[TargetScope, str] = {v: k for k, v in _SCOPE_FROM_STR.items()}

_SCOPE_LABELS: dict[TargetScope, str] = {
    TargetScope.ALL_FILES:      "All Files (*)",
    TargetScope.DIRECTORY:      "Directory",
    TargetScope.DIR_BACKGROUND: r"Directory\Background",
}


class APIHandler(SimpleHTTPRequestHandler):
    """Handle both static file serving and /api/* routes."""

    manager: RegistryManager  # set at class level before serving

    def __init__(self, *args, **kwargs):
        # Serve files from the static directory
        super().__init__(*args, directory=str(_STATIC_DIR), **kwargs)

    # Suppress default request logging
    def log_message(self, format, *args):
        pass

    # ── Routing ─────────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/entries":
            self._handle_list_entries()
        elif path.startswith("/api/entry/"):
            key_name = path.split("/api/entry/", 1)[1]
            self._handle_get_entry(key_name)
        elif path == "/api/status":
            self._json_response({
                "admin": is_admin(),
                "classic_menu": self.manager.is_classic_menu_forced(),
            })
        elif path == "/api/logs":
            self._handle_get_logs()
        elif path == "/api/logs/backups":
            self._handle_list_backups()
        elif path == "/api/open-log-folder":
            log_dir = str(_APP_DIR / "logs")
            os.makedirs(log_dir, exist_ok=True)
            os.startfile(log_dir)
            self._json_response({"ok": True, "path": log_dir})
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        body = self._read_body()

        if path == "/api/entries":
            self._handle_add_entry(body)
        elif path == "/api/pick-file":
            self._handle_pick_file()
        elif path == "/api/win11-menu":
            self._handle_toggle_win11(body)
        elif path == "/api/logs/clear":
            self._handle_clear_logs()
        elif path == "/api/logs/restore":
            self._handle_restore_logs(body)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path.startswith("/api/entries/"):
            key_name = path.split("/api/entries/", 1)[1]
            self._handle_remove_entry(key_name)
        elif path.startswith("/api/logs/backups/"):
            filename = path.split("/api/logs/backups/", 1)[1]
            self._handle_delete_backup(filename)
        else:
            self._json_response({"error": "Not found"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        body = self._read_body()

        if path.startswith("/api/entries/"):
            key_name = path.split("/api/entries/", 1)[1]
            self._handle_edit_entry(key_name, body)
        else:
            self._json_response({"error": "Not found"}, 404)

    # ── API Handlers ────────────────────────────────────────────

    def _handle_list_entries(self):
        """Return all entries grouped by scope with details."""
        result: list[dict] = []
        seen: set[str] = set()

        for scope in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
            entries = self.manager.list_entries(scope)
            for key_name in entries:
                if key_name not in seen:
                    seen.add(key_name)
                    # Gather all scopes this key exists in
                    scopes = []
                    for s in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
                        if key_name in self.manager.list_entries(s):
                            scopes.append(_SCOPE_TO_STR[s])

                    details = self.manager.read_entry_details(scope, key_name)
                    result.append({
                        "key_name": key_name,
                        "display_name": details["display_name"] if details else key_name,
                        "icon": details.get("icon") if details else None,
                        "command": details.get("command") if details else None,
                        "scopes": scopes,
                    })

        self._json_response(result)

    def _handle_get_entry(self, key_name: str):
        """Return details for a specific entry."""
        for scope in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
            details = self.manager.read_entry_details(scope, key_name)
            if details:
                scopes = []
                for s in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
                    if key_name in self.manager.list_entries(s):
                        scopes.append(_SCOPE_TO_STR[s])

                details["key_name"] = key_name
                details["scopes"] = scopes
                self._json_response(details)
                return

        self._json_response({"error": "Not found"}, 404)

    def _handle_add_entry(self, body: dict):
        """Add a new context-menu entry."""
        try:
            scopes = [_SCOPE_FROM_STR[s] for s in body.get("scopes", ["all_files"])]
            entry = MenuEntry(
                key_name=body["key_name"],
                display_name=body["display_name"],
                exe_path=body["exe_path"],
                icon=body.get("icon"),
                scopes=scopes,
                extensions=body.get("extensions", []),
                command_template=body.get("command_template", '"{exe_path}" "{target}"'),
            )
            self.manager.add_entry(entry)
            self._json_response({"success": True, "key_name": entry.key_name})
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_remove_entry(self, key_name: str):
        """Remove an entry from all its scopes."""
        try:
            scopes = []
            for s in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
                if key_name in self.manager.list_entries(s):
                    scopes.append(s)

            if not scopes:
                self._json_response({"error": "Not found"}, 404)
                return

            entry = MenuEntry(
                key_name=key_name,
                display_name="",
                exe_path="C:\\dummy.exe",
                scopes=scopes,
            )
            self.manager.remove_entry(entry)
            self._json_response({"success": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_edit_entry(self, key_name: str, body: dict):
        """Edit an entry: remove old scopes, re-add with new ones."""
        try:
            # Find current scopes
            current_scopes = []
            details = None
            for s in (TargetScope.ALL_FILES, TargetScope.DIRECTORY, TargetScope.DIR_BACKGROUND):
                if key_name in self.manager.list_entries(s):
                    current_scopes.append(s)
                    if details is None:
                        details = self.manager.read_entry_details(s, key_name)

            if not current_scopes or not details:
                self._json_response({"error": "Not found"}, 404)
                return

            # Extract exe_path from command
            cmd = details.get("command", "")
            if cmd.startswith('"'):
                exe_path = cmd.split('"')[1]
            else:
                exe_path = cmd.split()[0] if cmd else ""

            # Remove from old scopes
            old_entry = MenuEntry(
                key_name=key_name,
                display_name=details["display_name"],
                exe_path=exe_path or "C:\\dummy.exe",
                scopes=current_scopes,
            )
            self.manager.remove_entry(old_entry)

            # Re-add with new scopes
            new_scopes = [_SCOPE_FROM_STR[s] for s in body.get("scopes", [])]
            new_entry = MenuEntry(
                key_name=key_name,
                display_name=body.get("display_name", details["display_name"]),
                exe_path=body.get("exe_path", exe_path),
                icon=body.get("icon", details.get("icon")),
                scopes=new_scopes,
                extensions=body.get("extensions", []),
            )
            self.manager.add_entry(new_entry)
            self._json_response({"success": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_pick_file(self):
        """Open native file dialog in a separate thread to avoid blocking."""
        import tkinter as tk
        from tkinter import filedialog

        result = {"path": None}

        def pick():
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            path = filedialog.askopenfilename(
                title="Select Application (.exe)",
                filetypes=[("Executables", "*.exe"), ("All Files", "*.*")],
            )
            root.destroy()
            result["path"] = path or None

        t = threading.Thread(target=pick)
        t.start()
        t.join(timeout=120)

        self._json_response(result)

    def _handle_toggle_win11(self, body: dict):
        """Toggle Windows 11 classic/modern context menu."""
        try:
            action = body.get("action", "toggle")
            if action == "enable":
                self.manager.force_classic_menu()
            elif action == "disable":
                self.manager.restore_modern_menu()
            else:
                # toggle
                if self.manager.is_classic_menu_forced():
                    self.manager.restore_modern_menu()
                else:
                    self.manager.force_classic_menu()

            restart = body.get("restart_explorer", False)
            if restart:
                self.manager.restart_explorer()

            self._json_response({
                "success": True,
                "classic_menu": self.manager.is_classic_menu_forced(),
            })
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    # ── Log Handlers ───────────────────────────────────────────

    def _handle_get_logs(self):
        """Return the last N lines of the log file."""
        try:
            if _LOG_FILE.exists():
                lines = _LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
            else:
                lines = []
            backup_count = len(list(_LOG_BACKUP_DIR.glob("*.bak"))) if _LOG_BACKUP_DIR.exists() else 0
            self._json_response({
                "lines": lines[-10:],
                "total": len(lines),
                "backup_count": backup_count,
            })
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_list_backups(self):
        """Return all backup files sorted newest first."""
        try:
            backups = []
            if _LOG_BACKUP_DIR.exists():
                for f in sorted(_LOG_BACKUP_DIR.glob("*.bak"), reverse=True):
                    stat = f.stat()
                    backups.append({
                        "filename": f.name,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "lines": len(f.read_text(encoding="utf-8", errors="replace").splitlines()),
                    })
            self._json_response(backups)
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_clear_logs(self):
        """Backup current log with timestamp, then truncate it."""
        import shutil
        try:
            if _LOG_FILE.exists() and _LOG_FILE.stat().st_size > 0:
                _LOG_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_path = _LOG_BACKUP_DIR / f"context_menu_{ts}.log.bak"
                shutil.copy2(_LOG_FILE, backup_path)
                _LOG_FILE.write_text("", encoding="utf-8")
            self._json_response({"success": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_restore_logs(self, body: dict):
        """Restore log from a specific backup file."""
        try:
            filename = body.get("filename", "")
            if not filename:
                self._json_response({"error": "No filename specified"}, 400)
                return
            backup_path = _LOG_BACKUP_DIR / filename
            if not backup_path.exists() or not str(backup_path).startswith(str(_LOG_BACKUP_DIR)):
                self._json_response({"error": "Backup not found"}, 404)
                return
            backup_content = backup_path.read_text(encoding="utf-8", errors="replace")
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(backup_content)
            backup_path.unlink()
            self._json_response({"success": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    def _handle_delete_backup(self, filename: str):
        """Permanently delete a specific backup file."""
        try:
            backup_path = _LOG_BACKUP_DIR / filename
            if not backup_path.exists() or not str(backup_path).startswith(str(_LOG_BACKUP_DIR)):
                self._json_response({"error": "Backup not found"}, 404)
                return
            backup_path.unlink()
            self._json_response({"success": True})
        except Exception as e:
            self._json_response({"error": str(e)}, 400)

    # ── Utilities ───────────────────────────────────────────────

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    def _json_response(self, data, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# ── Server launchers ───────────────────────────────────────────

_server_instance: HTTPServer | None = None


def start_server() -> None:
    """Start the HTTP server (headless — no browser, no webview).

    Used by gui.py to run the API in a background thread.
    Blocks until server_close() is called or the process exits.
    """
    global _server_instance
    APIHandler.manager = RegistryManager(dry_run=False)

    _server_instance = HTTPServer(("127.0.0.1", _PORT), APIHandler)
    url = f"http://127.0.0.1:{_PORT}"
    log.info("Server running at %s", url)
    print(f"\n  [OK] Server listening on {url}")

    _server_instance.serve_forever()


def stop_server() -> None:
    """Gracefully shut down the running HTTP server."""
    global _server_instance
    if _server_instance:
        _server_instance.shutdown()
        _server_instance.server_close()
        _server_instance = None


def start_gui() -> None:
    """Legacy launcher — start server + open default browser."""
    if not is_admin():
        print("  ⚠  Not running as Administrator — add/remove/edit will fail.")
        print("     Right-click your terminal → 'Run as administrator'.\n")

    APIHandler.manager = RegistryManager(dry_run=False)

    server = HTTPServer(("127.0.0.1", _PORT), APIHandler)
    url = f"http://127.0.0.1:{_PORT}"
    log.info("Server running at %s", url)
    print(f"\n  ✔ GUI running at {url}")
    print("  Press Ctrl+C to stop.\n")

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    start_gui()
