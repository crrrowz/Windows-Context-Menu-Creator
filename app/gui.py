"""
Embedded webview entry point — opens the app as a native desktop window.

Replaces the browser-based launch with pywebview, giving the app
a proper title bar, no URL bar, and its own taskbar presence.
"""

from __future__ import annotations

import os
import sys
import time
import traceback
import threading
import urllib.request

_URL = "http://127.0.0.1:8787"
_MUTEX_NAME = "Global\\ContextMenuCreator_SingleInstance"
_mutex_handle = None


def _acquire_single_instance_lock() -> bool:
    """Try to acquire a system-wide mutex. Returns True if this is the only instance."""
    global _mutex_handle
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ERROR_ALREADY_EXISTS = 183

        _mutex_handle = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(_mutex_handle)
            _mutex_handle = None
            return False
        return True
    except Exception:
        return True  # If mutex fails, allow launch anyway


def _focus_existing_window():
    """Try to bring the existing instance's window to the foreground."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Context Menu Creator")
        if hwnd:
            SW_RESTORE = 9
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass

# Crash log in the centralized app data folder
_CRASH_DIR = os.path.join(os.environ.get("TEMP", r"C:\temp"), "ContextMenuCreator")
os.makedirs(_CRASH_DIR, exist_ok=True)
_CRASH_LOG = os.path.join(_CRASH_DIR, "crash.log")


def _log_crash(msg: str) -> None:
    """Append error info to crash.log for debugging frozen builds."""
    try:
        with open(_CRASH_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _wait_for_server(url: str, timeout: float = 10.0) -> bool:
    """Block until the HTTP server responds (or timeout)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.15)
    return False


def _run_server() -> None:
    """Wrapper around start_server that catches and logs crashes."""
    try:
        from app.server import start_server
        start_server()
    except Exception:
        _log_crash("SERVER CRASH:\n" + traceback.format_exc())


def launch() -> None:
    """Show window instantly with loading page, then navigate once server is ready."""
    try:
        # Single-instance guard
        if not _acquire_single_instance_lock():
            _focus_existing_window()
            sys.exit(0)

        from app.safety import is_admin
        if not is_admin():
            _log_crash("WARNING: Not running as Administrator")

        import webview
        from pathlib import Path

        # Resolve loading page as a file:/// URL
        if getattr(sys, 'frozen', False):
            _base = Path(sys._MEIPASS) / 'static'
        else:
            _base = Path(__file__).parent.parent / 'static'
        loading_url = (_base / 'loading.html').as_uri()
        icon_path = str(_base / 'icon.ico')

        class WindowAPI:
            """Exposed to JS as `pywebview.api.*`"""
            def __init__(self, win):
                self._win = win

            def minimize(self):
                self._win.minimize()

            def toggle_maximize(self):
                self._win.toggle_fullscreen()

            def close(self):
                self._win.destroy()

        # Show the window IMMEDIATELY with loading page
        window = webview.create_window(
            title="Context Menu Creator",
            url=loading_url,
            width=1100,
            height=720,
            min_size=(800, 500),
            resizable=True,
            frameless=True,
            background_color='#0a0a12',
        )

        api = WindowAPI(window)
        window.expose(api.minimize, api.toggle_maximize, api.close)

        def _set_window_icon():
            """Set the taskbar/title icon via Win32 API."""
            try:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                shell32 = ctypes.windll.shell32

                # Find the window by title
                hwnd = user32.FindWindowW(None, "Context Menu Creator")
                if not hwnd:
                    return

                # Load icon from .ico file
                IMAGE_ICON = 1
                LR_LOADFROMFILE = 0x0010
                LR_DEFAULTSIZE = 0x0040
                ico = user32.LoadImageW(
                    0, icon_path, IMAGE_ICON, 0, 0,
                    LR_LOADFROMFILE | LR_DEFAULTSIZE
                )
                if not ico:
                    return

                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, ico)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, ico)
            except Exception:
                pass  # Non-critical — fallback to default icon

        def _boot_server_then_navigate():
            """Start server + navigate once ready (runs after webview is live)."""
            _set_window_icon()

            server_thread = threading.Thread(target=_run_server, daemon=True)
            server_thread.start()

            ready = _wait_for_server(_URL)
            if ready:
                window.load_url(_URL)
            else:
                _log_crash("Server did not become ready within 10s timeout")

        # Start the server AFTER the webview event loop begins
        webview.start(func=_boot_server_then_navigate)

        os._exit(0)

    except Exception:
        _log_crash("LAUNCH CRASH:\n" + traceback.format_exc())
        os._exit(1)


if __name__ == "__main__":
    launch()
