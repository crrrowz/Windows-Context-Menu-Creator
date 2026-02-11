"""
Safety utilities — run BEFORE any registry operation.
"""

import ctypes
import os
from pathlib import Path

from app.logger_setup import get_logger

log = get_logger("safety")


def is_admin() -> bool:
    """Return True if the current process has Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        # Non-Windows fallback (should never hit in production)
        return os.getuid() == 0  # type: ignore[attr-defined]


def require_admin() -> None:
    """Raise PermissionError immediately if not elevated."""
    if not is_admin():
        msg = (
            "This tool must be run as Administrator.\n"
            "Right-click your terminal → 'Run as administrator'."
        )
        log.critical(msg)
        raise PermissionError(msg)


def validate_exe_path(path: str) -> Path:
    """
    Confirm the executable exists, is a file, and ends with .exe.
    Returns a resolved Path object.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Executable not found: {p}")
    if not p.is_file():
        raise FileNotFoundError(f"Path is not a file: {p}")
    if p.suffix.lower() != ".exe":
        log.warning("Path does not end with .exe — may not be a valid executable: %s", p)
    log.debug("Validated executable: %s", p)
    return p


def validate_icon_path(path: str | None) -> str | None:
    """
    Validate an icon path.  Accepts:
      - "C:\\path\\to\\app.exe"        (icon index 0 implied)
      - "C:\\path\\to\\app.exe,3"      (specific icon index)
      - "C:\\path\\to\\icon.ico"
    Returns the original string unchanged if valid, None if input is None.
    """
    if path is None:
        return None

    # Strip optional icon index suffix (e.g. ",0")
    raw = path.split(",")[0].strip()
    p = Path(raw).resolve()

    if not p.exists():
        raise FileNotFoundError(f"Icon source not found: {p}")
    if not p.is_file():
        raise FileNotFoundError(f"Icon path is not a file: {p}")

    log.debug("Validated icon: %s", path)
    return path
