# python.exe -m PyInstaller --clean --noconfirm MortarAid.spec



# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path


def collect_tk_runtime_binaries():
    binaries = []
    seen = set()
    base_prefix = Path(sys.base_prefix)
    candidate_dirs = [
        base_prefix / "Library" / "bin",
        base_prefix / "DLLs",
    ]
    required_dll_names = (
        "tcl86t.dll",
        "tk86t.dll",
        "libexpat.dll",
        "libssl-3-x64.dll",
        "libcrypto-3-x64.dll",
        "liblzma.dll",
        "libbz2.dll",
        "ffi.dll",
    )

    for folder in candidate_dirs:
        for dll_name in required_dll_names:
            dll_path = folder / dll_name
            if dll_path.exists():
                key = str(dll_path).lower()
                if key not in seen:
                    binaries.append((str(dll_path), "."))
                    seen.add(key)

    return binaries


tk_runtime_binaries = collect_tk_runtime_binaries()


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=tk_runtime_binaries,
    datas=[
        ('img\\guide-step1.png', 'img'),
        ('img\\guide-step2.png', 'img'),
        ('img\\icon.ico', 'img'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'numpy',
        'pandas',
        'scipy',
        'matplotlib',
        'PIL.ImageQt',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'IPython',
        'jupyter',
        'notebook',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MortarAid',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    uac_admin=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['img\\icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='MortarAid',
)
