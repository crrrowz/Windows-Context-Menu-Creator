"""
Centralized logging configuration.
All modules import `get_logger` to get a child logger
scoped to their module name.
"""

import logging
import os
import sys
from pathlib import Path

# Logs always go to a fixed, user-accessible location.
_LOG_DIR = Path(os.environ.get("TEMP", r"C:\temp")) / "ContextMenuCreator" / "logs"
_LOG_FILE = _LOG_DIR / "context_menu.log"
_INITIALIZED = False


def _init_root_logger() -> None:
    """Configure the root logger once."""
    global _INITIALIZED
    if _INITIALIZED:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger("ctxmenu")
    root.setLevel(logging.DEBUG)

    # ── File handler (verbose) ──────────────────────────────────
    fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s → %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # ── Console handler (compact) ───────────────────────────────
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s │ %(message)s"))

    root.addHandler(fh)
    root.addHandler(ch)
    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the `ctxmenu` namespace."""
    _init_root_logger()
    return logging.getLogger(f"ctxmenu.{name}")
