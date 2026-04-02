from pathlib import Path

# PyInstaller spec for Windows build

block_cipher = None

project_root = Path(__file__).resolve().parents[2]

datas = [
    (str(project_root / "app" / "templates"), "app/templates"),
    (str(project_root / "app" / "static"), "app/static"),
    (str(project_root / "Plot Bunny.html"), "Plot Bunny.html"),
]

a = Analysis(
    [str(project_root / "run_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    a.datas,
    [],
    name="data-analysis-tool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

