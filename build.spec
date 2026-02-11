# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Context Menu Creator.

Build with:
    pyinstaller build.spec

Output:
    dist/ContextMenuCreator.exe
"""

import os
import sys

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('app', 'app'),
    ],
    hiddenimports=[
        'webview',
        'app.config',
        'app.registry_manager',
        'app.safety',
        'app.logger_setup',
        'app.server',
        'app.gui',
        'app.examples',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Context Menu Creator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # --windowed: no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon='static/icon.ico',
)
