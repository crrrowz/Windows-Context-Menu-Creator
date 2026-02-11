# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.0.0] — 2026-02-11

### Added

- **Native desktop app** — Standalone `.exe` window via pywebview with custom frameless titlebar (minimize, maximize, close).
- **Single-instance enforcement** — Windows named mutex prevents duplicate launches; focuses existing window instead.
- **Internationalization (i18n)** — Full Arabic and English support with dynamic language switching.
- **RTL layout** — Complete right-to-left support for Arabic, including CSS logical properties throughout.
- **Dark / Light themes** — Theme toggle with persistence via localStorage.
- **SVG icon system** — All UI icons replaced with inline SVG (no emoji dependencies).
- **Loading splash screen** — Instant `loading.html` shown while the server boots, eliminating blank-window delay.
- **Titlebar menu bar** — File, View, and Help dropdown menus in the custom titlebar.
- **Extension summary chips** — Selected extensions shown as removable chips with custom extension support.

### Changed

- **Project structure** — Python modules moved into `app/` package; documentation moved to `docs/`.
- **Build entry point** — PyInstaller now bundles from `main.py` with `app/` as a package.
- **Taskbar icon** — Set at runtime via Win32 API (`LoadImageW` + `SendMessageW`).

### Fixed

- RTL dropdown menus no longer clip off-screen.
- Filter tabs no longer double-reverse in RTL mode.
- Search box icon and padding use CSS logical properties for correct RTL alignment.

---

## [1.0.0] — 2026-02-10

### Added

- **Web GUI** — Full browser-based interface at `localhost:8787` with dark theme.
- **Entry management** — Add, edit, and remove context menu entries via GUI or CLI.
- **Multi-scope support** — Register entries for All Files, Directories, Directory Background, or specific file extensions.
- **Extension picker** — Visual category-based picker with 80+ file extensions across 8 categories (Code, Web, Data, Docs, Images, Audio, Video, Archives).
- **Windows 11 classic menu toggle** — Force the full context menu with one click (auto-restarts Explorer).
- **Live log sidebar** — Real-time log feed with 3-second polling and hash-based change detection.
- **Timestamped log backups** — Clear logs with automatic timestamped backup; browse, restore, or delete backups from a dedicated popup.
- **CLI mode** — Interactive terminal interface with `add`, `remove`, `edit`, `list`, and `doctor` commands.
- **Dry-run mode** — Preview all registry operations without writing (`--dry-run`).
- **Auto icon detection** — Automatically derives icon path from selected executable.
- **File picker** — Native Windows file dialog integration for selecting executables.
- **Search & filter** — Filter entries by scope or search by name/command.
- **Admin detection** — Status badge shows whether the app is running with Administrator privileges.
- **Modular frontend** — Split into `app.js`, `extensions.js`, `modal.js`, `logs.js` for maintainability.

### Security

- All registry operations require Administrator privileges (enforced at runtime).
- File paths are validated before any registry write.
- Backup file deletion is restricted to the `logs/backups/` directory (path traversal prevention).
