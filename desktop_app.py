import os
import sys
import traceback
from pathlib import Path

import webview

from desktop_api import DesktopAPI

def _resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return str(Path(base) / rel_path)
    return str(Path(__file__).resolve().parent / rel_path)


def _ensure_dirs() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("plots").mkdir(parents=True, exist_ok=True)


def _show_error(title: str, message: str) -> None:
    # 在 Windows “无控制台”模式下，用原生弹窗提示错误（否则用户看不到任何报错）
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        pass


def _write_log(text: str) -> None:
    try:
        Path("PlotBunny.log").write_text(text, encoding="utf-8")
    except Exception:
        pass


def main() -> None:
    try:
        _ensure_dirs()
        # 让模板/静态资源在 PyInstaller 环境下也能被找到（供 HTML 引用 favicon 等）
        os.environ.setdefault("APP_STATIC_DIR", _resource_path("app/static"))
    except Exception:
        _write_log(traceback.format_exc())
        _show_error(
            "Plot Bunny",
            "启动失败：初始化失败。\n\n已生成日志：PlotBunny.log（与 exe 同目录）",
        )
        return

    html_path = Path(_resource_path("Plot Bunny.html")).resolve()
    if not html_path.exists():
        _show_error("Plot Bunny", "找不到前端页面：Plot Bunny.html")
        return

    try:
        api = DesktopAPI()
        window = webview.create_window(
            "Plot Bunny",
            url=html_path.as_uri(),
            width=1100,
            height=780,
            min_size=(980, 640),
            js_api=api,
        )
        api._window = window
        webview.start(debug=False)
    except Exception as exc:
        # 最常见：目标机器缺 WebView2 Runtime 或 webview 后端初始化失败
        _write_log(traceback.format_exc())
        _show_error(
            "Plot Bunny",
            "无法初始化桌面窗口（WebView）。\n\n"
            "请确保已安装 Microsoft Edge WebView2 Runtime，然后重试。\n\n"
            f"调试信息：{exc}\n\n已生成日志：PlotBunny.log（与 exe 同目录）",
        )


if __name__ == "__main__":
    main()

