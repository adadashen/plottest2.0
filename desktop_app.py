import os
import sys
import socket
import threading
import time
import traceback
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn
import webview


HOST = "127.0.0.1"
BASE_PORT = 9876
MAX_PORT_TRIES = 20


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


def _write_port_file(port: int) -> None:
    try:
        Path("PORT.txt").write_text(str(port), encoding="utf-8")
    except Exception:
        pass


def _find_free_port(host: str, start_port: int, max_tries: int) -> int:
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
            except OSError:
                continue
            return port
    return start_port


def _wait_until_healthy(port: int, timeout_s: float = 20.0) -> bool:
    deadline = time.time() + timeout_s
    url = f"http://{HOST}:{port}/health"
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=0.8) as resp:
                if resp.status == 200:
                    return True
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(0.3)
    return False


def _start_server_in_thread(port: int) -> tuple[uvicorn.Server, threading.Thread]:
    _ensure_dirs()
    _write_port_file(port)

    os.environ.setdefault("APP_TEMPLATES_DIR", _resource_path("app/templates"))
    os.environ.setdefault("APP_STATIC_DIR", _resource_path("app/static"))

    config = uvicorn.Config(
        "app.main:app",
        host=HOST,
        port=port,
        reload=False,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)

    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    return server, t


def main() -> None:
    try:
        port = _find_free_port(HOST, BASE_PORT, MAX_PORT_TRIES)
        server, _ = _start_server_in_thread(port)
    except Exception:
        _write_log(traceback.format_exc())
        _show_error(
            "Plot Bunny",
            "启动失败：无法初始化后端服务。\n\n已生成日志：PlotBunny.log（与 exe 同目录）",
        )
        return

    if not _wait_until_healthy(port, timeout_s=25.0):
        _write_log(f"Backend did not become healthy on port {port}.\n")
        _show_error(
            "Plot Bunny",
            f"后端服务启动失败（端口 {port}）。\n\n请检查是否被安全软件拦截，或端口被占用。",
        )
        return

    url = f"http://{HOST}:{port}/"

    def on_closed():
        server.should_exit = True

    try:
        window = webview.create_window(
            "Plot Bunny",
            url=url,
            width=1100,
            height=780,
            min_size=(980, 640),
        )
        window.events.closed += on_closed
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
        server.should_exit = True


if __name__ == "__main__":
    main()

