# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['SuporteApp.py'],
    pathex=[],
    binaries=[],
    datas=[('ico.ico', '.'), ('dark_theme_preview.png', '.'), ('light_theme_preview.png', '.'), ('sepia_theme_preview.png', '.'), ('sepia_background.png', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SuporteApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir='.',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon=['ico.ico'],
)
