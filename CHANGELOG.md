# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
