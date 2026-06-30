# Finarix

Personal finance tracker — monthly budget, net worth tracking, encrypted data.  
Built with Python / Tkinter. Packaged as a standalone Windows `.exe` via PyInstaller.

---

## Features

- Monthly budget: planned vs actual (income, fixed expenses, variable expenses)
- Net worth section: bank account, assets, liabilities
- Bilan (actual) vs Prévision (forecast) modes
- Data encrypted with AES-256 (Fernet + PBKDF2, 480 000 iterations)
- Backup / restore as ZIP
- Multi-language: French · English · Vietnamese
- HTML export (PDF via browser print)

---

## Prerequisites

Install **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — it manages Python and all dependencies automatically, no separate Python install needed.

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Run in development

```powershell
# Clone / open the project folder, then:
uv run main.py
```

`uv` reads `pyproject.toml`, installs `cryptography`, and launches the app.  
Data is stored in `<project-root>/data/` during development.

---

## Build the Windows executable

```powershell
uv run --with pyinstaller pyinstaller Finarix.spec --noconfirm
```

The output is `dist/Finarix.exe` — a single, self-contained file with no installer required.

> **Before rebuilding:** close the running `Finarix.exe` first, or the build will fail with a permission error.
>
> ```powershell
> Stop-Process -Name "Finarix" -Force -ErrorAction SilentlyContinue
> ```

When running as a packaged `.exe`, data is stored in `%APPDATA%\Finarix\data\` so it survives rebuilds.

---

## Project structure

```
Finarix/
├── main.py              # Entry point (4 lines)
├── pyproject.toml       # Dependencies (uv)
├── uv.lock              # Locked dependency versions
├── Finarix.spec         # PyInstaller build spec
└── finarix/
    ├── app.py           # Main window (wires UI + logic + login)
    ├── config.py        # Colors, DEFAULT_DATA
    ├── finance.py       # Pure calculation helpers
    ├── i18n.py          # Translations (FR / EN / VI)
    ├── storage.py       # Encrypted file I/O
    ├── auth.py          # Password setup & verification
    ├── export.py        # HTML export, ZIP backup/restore
    ├── ui_mixin.py      # Widget construction
    ├── logic_mixin.py   # Event handlers & recalculation
    └── dialogs/
        ├── login.py     # Login / first-time setup dialog
        └── forward.py   # "Apply to future months" dialog
```

---

## Data & encryption

- Each month is saved as `YYYY-MM.json` (binary, Fernet-encrypted) in the data folder.
- The encryption key is derived from your password using PBKDF2-HMAC-SHA256 (480 000 iterations).
- A `.auth` file stores the salt and an encrypted verifier token — the password itself is never saved.
- Use **☰ → Sauvegarder données** to export a ZIP backup (decrypted JSON inside the ZIP).

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `cryptography` | AES-256 encryption (Fernet) |
| `pyinstaller` | Build-time only — packages the app as `.exe` |

Python stdlib only otherwise (Tkinter, json, zipfile, webbrowser…).
