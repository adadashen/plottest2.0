from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 在部分 CI 环境中 spec 执行时可能没有 __file__，因此基于当前工作目录（仓库根目录）定位
project_root = Path.cwd().resolve()

datas = [
    (str(project_root / "app" / "templates"), "app/templates"),
    (str(project_root / "app" / "static"), "app/static"),
    # 可选独立页（不是桌面主入口，但一起带上便于调试/分发）
    (str(project_root / "Plot Bunny.html"), "."),
]

# 让 pywebview 在 onefile 下稳定工作：收集子模块与数据文件
hiddenimports = collect_submodules("webview")
datas += collect_data_files("webview")

a = Analysis(
    [str(project_root / "desktop_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="PlotBunny",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台黑框
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

