# Contributing to Windows Context Menu Creator

Thank you for your interest in contributing! This guide will help you get started.

---

## 🛠️ Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/crrrowz/Windows-Context-Menu-Creator.git
   cd Windows-Context-Menu-Creator
   ```

2. **Run in dry-run mode** (safe, no registry writes)
   ```bash
   python main.py add --dry-run
   ```

3. **Launch the GUI**
   ```bash
   python main.py --gui
   ```
   The app opens at `http://localhost:8787`.

### Requirements

- Python 3.10+
- Windows 10 or 11
- No external packages needed (stdlib only)

---

## 📁 Project Structure

| File | Purpose |
|---|---|
| `config.py` | Data models (`MenuEntry`, `TargetScope`) — no side-effects |
| `safety.py` | Admin checks and path validation |
| `registry_manager.py` | All `winreg` operations — the only module touching the registry |
| `server.py` | HTTP API server bridging the GUI to registry operations |
| `main.py` | CLI entry point and `--gui` launcher |
| `logger_setup.py` | Centralized logging with file rotation |
| `static/` | Frontend files (HTML, CSS, JS) |

---

## 📐 Coding Guidelines

### Python

- **Type hints** on all function signatures.
- **Docstrings** for every public function and class.
- Follow existing formatting patterns (no auto-formatter enforced, but keep it consistent).
- All registry operations go through `registry_manager.py` — never import `winreg` elsewhere.

### JavaScript

- All functions are in the global scope (no modules/bundler).
- Files are loaded in order: `app.js` → `extensions.js` → `modal.js` → `logs.js`.
- Shared utilities (`toast`, `esc`) live in `app.js`.

### CSS

- Use CSS custom properties defined in `:root` for all colors, spacing, and radii.
- Follow the existing section comment pattern (`/* ── Section Name ─── */`).

---

## 🔀 Pull Request Process

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** — keep commits focused and descriptive.

3. **Test thoroughly**:
   - Run the GUI and verify your changes visually.
   - Test with `--dry-run` if your changes affect registry operations.
   - Test on both Windows 10 and 11 if possible.

4. **Submit a PR** with:
   - A clear description of what changed and why.
   - Screenshots if the change is visual.
   - Note any breaking changes.

---

## 🐛 Reporting Bugs

When filing an issue, please include:

- **OS version** (Windows 10/11, build number)
- **Python version** (`python --version`)
- **Steps to reproduce** the issue
- **Expected vs. actual behavior**
- **Log output** (from the GUI sidebar or `logs/context_menu.log`)

---

## 💡 Feature Requests

Open an issue with the `enhancement` label. Describe:

- **What** you want added
- **Why** it would be useful
- **How** it could work (optional, but helpful)

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
