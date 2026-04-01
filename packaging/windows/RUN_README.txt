数据分析工具（Windows 可执行版）

1) 运行方式
- 双击 data-analysis-tool.exe
- 默认会在本机启动后端服务: http://127.0.0.1:8001/
- 会自动打开浏览器进入主界面（如果没有自动打开，请手动访问上面地址）

2) 数据与输出位置
- 数据库: data/analysis.db
- 上传文件: data/uploads/
- 图表输出: plots/

3) 常见问题
- 端口占用: 设置环境变量 APP_PORT（例如 8002）后再启动
- 禁止自动打开浏览器: 设置 APP_OPEN_BROWSER=0

