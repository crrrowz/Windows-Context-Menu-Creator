# Development Roadmap

This document outlines the planned evolution of Windows Context Menu Creator from a Python script into a fully self-contained native desktop application.

---

## 🎯 Vision

Transform the project from a **terminal-launched Python script** that opens the default browser into a **single `.exe` file** that runs as a standalone native-feeling desktop application — no Python installation required, no external browser dependency.

---

## Phase 1: Embedded Webview (Replace External Browser)

### Problem

Currently, `python main.py --gui` starts an HTTP server and opens the user's default browser. This has drawbacks:

- The app feels like a "web page", not a desktop tool.
- The browser tab can be accidentally closed or lost among other tabs.
- Users see the `localhost:8787` URL bar, which feels unpolished.
- No control over window size, title bar, or system tray behavior.

### Solution

Use **[pywebview](https://pywebview.flowrl.com/)** to embed a lightweight webview window. The app opens as its own desktop window with a proper title bar, icon, and no URL bar — while still rendering the same HTML/CSS/JS frontend internally.

### Implementation Plan

1. **Install `pywebview`**:
   ```bash
   pip install pywebview
   ```

2. **Create `gui.py`** — New entry point that replaces browser launch:
   ```python
   import webview
   import threading
   from server import start_server  # refactored to not auto-open browser

   def launch():
       # Start HTTP server on background thread
       server_thread = threading.Thread(target=start_server, daemon=True)
       server_thread.start()

       # Open embedded window (not a browser)
       webview.create_window(
           title="Context Menu Creator",
           url="http://localhost:8787",
           width=1100,
           height=720,
           min_size=(800, 500),
           resizable=True,
       )
       webview.start()  # Blocks until window closes
   ```

3. **Refactor `server.py`**:
   - Extract `start_server()` function that only starts the HTTP listener.
   - Remove `webbrowser.open()` call.
   - Server shuts down cleanly when the webview window closes.

4. **Update `main.py`**:
   ```python
   if "--gui" in sys.argv:
       from gui import launch
       launch()
   ```

### Benefits

| Before | After |
|---|---|
| Opens Chrome/Edge/Firefox tab | Opens dedicated app window |
| URL bar visible (`localhost:8787`) | Clean title bar, no URL bar |
| Tab can be lost among browser tabs | Always its own window in taskbar |
| No control over window dimensions | Custom default size and min size |
| Browser must be installed | Uses system WebView2 (built into Windows 10/11) |

---

## Phase 2: Standalone `.exe` Packaging

### Problem

Users must have Python 3.10+ installed and run `python main.py` from a terminal. This is a barrier for non-developers and makes distribution difficult.

### Solution

Use **[PyInstaller](https://pyinstaller.org/)** to bundle the entire application — Python runtime, all modules, static assets, and the webview — into a single `.exe` file.

### Implementation Plan

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Create `build.spec`** (or use CLI flags):
   ```bash
   pyinstaller --onefile --windowed --name "ContextMenuCreator" \
       --add-data "static;static" \
       --add-data "logs;logs" \
       --icon "static/icon.ico" \
       gui.py
   ```

   Key flags:
   | Flag | Purpose |
   |---|---|
   | `--onefile` | Single `.exe` output |
   | `--windowed` | No console window on launch |
   | `--add-data` | Bundle `static/` folder inside the exe |
   | `--icon` | Custom app icon |

3. **Handle bundled paths** — PyInstaller changes the base path at runtime. Update `server.py` to resolve static files correctly:
   ```python
   import sys, os

   if getattr(sys, 'frozen', False):
       BASE_DIR = sys._MEIPASS  # PyInstaller temp folder
   else:
       BASE_DIR = os.path.dirname(__file__)

   STATIC_DIR = os.path.join(BASE_DIR, "static")
   ```

4. **Create app icon** — Design an `.ico` file for the window title bar and taskbar.

5. **Auto-elevate to Administrator** — Add a Windows manifest requesting admin on launch:
   ```xml
   <!-- app.manifest -->
   <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
   ```
   PyInstaller supports this via `--uac-admin` flag.

### Alternative: Nuitka

[Nuitka](https://nuitka.net/) compiles Python to C, producing a faster and smaller binary:

```bash
pip install nuitka
nuitka --standalone --onefile --windows-disable-console \
    --include-data-dir=static=static \
    --windows-icon-from-ico=static/icon.ico \
    gui.py
```

| Tool | Pros | Cons |
|---|---|---|
| **PyInstaller** | Mature, well-documented, fast builds | Larger output size (~30-50 MB) |
| **Nuitka** | Smaller binary, faster runtime, real compilation | Slower build process, needs C compiler |

### Final Output

```
dist/
└── ContextMenuCreator.exe   # Single file, ~30-50 MB
```

Double-click → app window opens → full functionality. No Python, no browser, no terminal.

---

## Phase 3: Polish & Distribution

### Tasks

- [ ] **App icon** — Design a proper `.ico` for the title bar, taskbar, and exe file.
- [ ] **System tray** — Minimize to tray instead of closing; right-click tray icon for quick actions.
- [ ] **Auto-update** — Check GitHub releases for new versions on startup.
- [ ] **Installer (optional)** — Use [NSIS](https://nsis.sourceforge.io/) or [Inno Setup](https://jrsoftware.org/isinfo.php) to create a proper `Setup.exe` with:
  - Start menu shortcut
  - Desktop shortcut
  - Uninstaller entry in "Add/Remove Programs"
- [ ] **Code signing** — Sign the `.exe` to avoid Windows SmartScreen warnings.
- [ ] **GitHub Releases** — Publish versioned `.exe` builds as GitHub Release assets.

---

## Dependency Summary

| Phase | New Dependencies |
|---|---|
| Phase 1 (Webview) | `pywebview` |
| Phase 2 (Exe) | `pyinstaller` or `nuitka` (build-time only) |
| Phase 3 (Polish) | None (tooling only) |

---

## Timeline Estimate

| Phase | Effort | Priority |
|---|---|---|
| Phase 1 — Embedded Webview | ~2 hours | 🔴 High |
| Phase 2 — Standalone `.exe` | ~3 hours | 🔴 High |
| Phase 3 — Polish & Distribution | ~4 hours | 🟡 Medium |
