# Windows Context Menu Creator

A powerful, GUI-based tool for managing Windows Explorer right-click context menu entries directly from your browser. Add, edit, and remove shell entries across multiple registry scopes — no manual `regedit` needed.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6?logo=windows)

---

## ✨ Features

- **Desktop app** — Native window via pywebview (no browser needed), with custom frameless titlebar
- **Web-based GUI** — Modern, dark-themed interface served at `localhost:8787`
- **Multi-language** — English and Arabic with full RTL support
- **Dark / Light themes** — Toggle between themes, persisted in localStorage
- **Multi-scope registration** — Target `All Files (*)`, `Directories`, `Directory Background`, or specific file extensions
- **Extension picker** — Visual category-based picker with 80+ common file extensions
- **Windows 11 support** — One-click toggle to force the classic context menu (bypasses "Show more options")
- **Live log sidebar** — Real-time log feed with 3-second polling, no manual refresh needed
- **Timestamped backups** — Clear logs safely; browse, restore, or delete past backups anytime
- **CLI mode** — Full interactive terminal interface for scripting and automation
- **Dry-run mode** — Preview all registry changes without writing anything
- **Auto icon detection** — Automatically extracts icon path from selected executables
- **Search & filter** — Instantly find entries by name, command, or scope

---

## 📸 Screenshots

> *Add screenshots of the GUI here before publishing.*

---

## 🚀 Getting Started

### Prerequisites

| Requirement | Details |
|---|---|
| **OS** | Windows 10 or 11 |
| **Python** | 3.10+ |
| **Privileges** | Must run as **Administrator** (registry writes require elevation) |

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/Windows-Context-Menu-Creator.git
cd Windows-Context-Menu-Creator
```

No external dependencies — the project uses only Python's standard library.

### Usage

#### Interactive CLI

```bash
python main.py
```

Launches a live interactive terminal with a menu to **add**, **remove**, **edit**, **list** entries, run diagnostics, and more — all from the command line.

#### Web GUI

```bash
python main.py --gui
```

Opens the app as a native desktop window (pywebview). No browser required.

#### Web GUI (browser fallback)

```bash
python main.py --browser
```

Opens your default browser to `http://localhost:8787` with the full visual interface.

#### Dry Run

```bash
python main.py --dry-run
```

Logs every registry operation without actually writing. Useful for previewing changes safely.

---

## 🏗️ Architecture

```
Windows-Context-Menu-Creator/
├── main.py                   # CLI entry point + --gui / --browser launcher
├── build.spec                # PyInstaller build configuration
├── requirements.txt          # Runtime dependencies (pywebview)
├── app/                      # Core Python package
│   ├── __init__.py
│   ├── gui.py                # Desktop launcher (pywebview + single-instance)
│   ├── server.py             # HTTP API server (REST + static file serving)
│   ├── registry_manager.py   # All Windows Registry (winreg) operations
│   ├── config.py             # Data models: MenuEntry, TargetScope
│   ├── safety.py             # Admin check, exe/icon path validation
│   ├── logger_setup.py       # Centralized logging configuration
│   └── examples.py           # Pre-built entry templates
├── static/
│   ├── index.html            # Main HTML shell (custom frameless titlebar)
│   ├── loading.html          # Instant loading splash page
│   ├── icon.ico              # Application icon
│   ├── css/
│   │   └── styles.css        # Full design system (dark/light, LTR/RTL)
│   ├── js/
│   │   ├── app.js            # Init, status, entries, filtering, rendering
│   │   ├── i18n.js           # Language & theme engine, SVG icon library
│   │   ├── extensions.js     # Extension picker (categories, chips, custom)
│   │   ├── modal.js          # Add/Edit/Delete modals + form handling
│   │   ├── menubar.js        # Titlebar menu dropdowns
│   │   └── logs.js           # Live log polling + backup browser
│   └── lang/
│       ├── en.json           # English translations (LTR)
│       └── ar.json           # Arabic translations (RTL)
└── docs/
    └── PYTHON_TO_WINDOWS_APP.md  # Conversion guide
```

### Module Responsibilities

| Module | Role |
|---|---|
| `app/config.py` | Pure data layer — `MenuEntry` dataclass and `TargetScope` enum. Zero side-effects. |
| `app/safety.py` | Pre-flight checks: admin privileges, exe path validation, icon path validation. |
| `app/registry_manager.py` | The **only** module that touches `winreg`. All read/write/delete operations. |
| `app/server.py` | HTTP API bridge between the web GUI and `RegistryManager`. Serves static files. |
| `app/gui.py` | Desktop shell — pywebview launcher, single-instance mutex, taskbar icon. |
| `app/logger_setup.py` | Configures file + console logging under `%TEMP%\ContextMenuCreator\logs`. |
| `main.py` | CLI entry point. `--gui` for desktop, `--browser` for browser, plain for CLI. |

---

## 🔌 API Reference

All endpoints are served at `http://localhost:8787`.

### Entries

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/entries` | List all entries across all scopes |
| `GET` | `/api/entry/<key>` | Get details for a specific entry |
| `POST` | `/api/entries` | Add a new entry |
| `PUT` | `/api/entries/<key>` | Edit an existing entry |
| `DELETE` | `/api/entries/<key>` | Remove an entry from all scopes |

### System

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | Check admin status and Win11 menu state |
| `POST` | `/api/win11-menu` | Toggle Windows 11 classic context menu |
| `POST` | `/api/pick-file` | Open native file picker dialog |

### Logs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/logs` | Get last 10 log lines + backup count |
| `POST` | `/api/logs/clear` | Backup current log with timestamp, then clear |
| `GET` | `/api/logs/backups` | List all backup files (date, size, line count) |
| `POST` | `/api/logs/restore` | Restore a specific backup (`{filename}`) |
| `DELETE` | `/api/logs/backups/<name>` | Permanently delete a backup file |

---

## 🔧 Registry Scopes

| Scope | Registry Path | Target |
|---|---|---|
| `ALL_FILES` | `HKCR\*\shell` | Right-click on any file |
| `DIRECTORY` | `HKCR\Directory\shell` | Right-click on a folder |
| `DIR_BACKGROUND` | `HKCR\Directory\Background\shell` | Right-click on empty space inside a folder |
| `EXTENSION` | `HKCR\.ext\shell` | Right-click on files with specific extensions |

---

## ⚠️ Important Notes

- **Always run as Administrator** — Registry writes to `HKEY_CLASSES_ROOT` require elevation.
- **Changes are immediate** — New context menu entries appear instantly in Explorer.
- **Win11 toggle restarts Explorer** — The classic menu toggle kills and restarts `explorer.exe`.
- **Backup your registry** — While the tool is safe, it's good practice to export `HKCR` before bulk operations.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
