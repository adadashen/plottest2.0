import os
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import uvicorn


def _resource_path(rel_path: str) -> str:
    """
    PyInstaller onefile/onedir 兼容的资源路径解析。
    """
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return str(Path(base) / rel_path)
    return str(Path(__file__).resolve().parent / rel_path)


def _ensure_dirs() -> None:
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("plots").mkdir(parents=True, exist_ok=True)


def _write_port_file(port: int) -> None:
    try:
        Path("PORT.txt").write_text(str(port), encoding="utf-8")
    except Exception:
        pass


def _wait_until_healthy(host: str, port: int, timeout_s: float = 20.0) -> bool:
    deadline = time.time() + timeout_s
    url = f"http://{host}:{port}/health"
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=0.8) as resp:
                if resp.status == 200:
                    return True
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(0.4)
    return False


def _open_browser_when_ready(host: str, port: int) -> None:
    def _worker():
        # 等后端 ready 再打开浏览器，避免“刚启动就打不开”造成误判
        _wait_until_healthy(host, port, timeout_s=20.0)
        try:
            webbrowser.open(f"http://{host}:{port}/")
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def main() -> None:
    # 固定本地地址与端口（分发版默认）
    host = "127.0.0.1"
    port = 8001
    open_browser = True

    _ensure_dirs()
    _write_port_file(port)

    # 让模板/静态资源在 PyInstaller 环境下也能被找到
    os.environ.setdefault("APP_TEMPLATES_DIR", _resource_path("app/templates"))
    os.environ.setdefault("APP_STATIC_DIR", _resource_path("app/static"))

    if open_browser:
        _open_browser_when_ready(host, port)

    uvicorn.run("app.main:app", host=host, port=port, reload=False, log_level="info")


if __name__ == "__main__":
    main()

