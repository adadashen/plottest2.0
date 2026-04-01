# Plot Bunny 分发包说明

本项目提供两种分发方式：

## 方式 A：Windows 双击启动（推荐）

直接双击项目根目录下的：

- `START_WINDOWS.bat`

脚本会自动：
- 创建 `.venv`
- 安装依赖（首次）
- 启动 Plot Bunny

默认地址：`http://127.0.0.1:8001/`

> 首次启动会慢一些（需要安装依赖），后续会快很多。
> 若 8001 被占用，启动脚本会自动切换到 8002/8003... 并在终端显示实际端口。

端口查看：
- 启动后项目根目录会生成 `PORT.txt`，里面就是当前端口。

提示：
- 正常使用请访问启动后自动打开的首页（若未自动打开，请按终端显示端口访问 `http://127.0.0.1:<端口>/`）
- `Plot Bunny.html` 为独立页（可选），需要先启动后端

## 方式 B：Windows EXE（可选）

说明：需要在 **Windows** 机器上打包生成 `data-analysis-tool.exe`（macOS 不能直接生成 Windows exe）。

- **打包**：在 Windows 上进入项目根目录，PowerShell 运行：

```powershell
.\packaging\windows\build.ps1
```

- **产物**：`dist\data-analysis-tool.exe`
- **运行**：双击 `data-analysis-tool.exe`，默认打开 `http://127.0.0.1:8001/`

## 方式 C：源码分发（macOS / Windows / Linux）

适合对方有 Python 环境（或愿意安装）。

- **准备**：安装 Python 3（建议 3.10+）
- **安装依赖**（项目根目录）：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- **启动**：

```bash
python run_app.py
```

默认地址：`http://127.0.0.1:8001/`

## 独立页（可选）

- 文件：`Plot Bunny.html`
- 需要先启动后端（默认 `http://127.0.0.1:8001`）

