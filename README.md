# 数据分析系统框架（FastAPI + Pandas + SQLite）

这是一个可运行的数据分析系统框架（后端 + 前端页面），包含以下能力：

- 数据上传与解析：支持上传 CSV/XLSX 并自动解析结构信息
- 数据分析：基础统计与表格数据预览（前12行）
- 数据作图：温度与压力随时间变化的双Y轴曲线图
- 数据存储：SQLite 存储数据集元信息
- Web API：对外提供 RESTful 接口
- 前端页面：浏览器内完成上传、分析查询与图表展示

## 1. 开发步骤（已按步骤实现）

1. 搭建项目结构与依赖
2. 搭建数据库层与数据模型
3. 实现上传解析服务（CSV/XLSX）
4. 实现分析服务（统计、预览）
5. 实现作图服务（时间双Y轴曲线）
6. 暴露 Web API 路由
7. 补充运行与验证说明
8. 增加前端页面（上传、数据列表、分析、作图展示）

## 2. 项目结构

```text
.
├── app
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── routers
│   │   ├── analysis.py
│   │   ├── datasets.py
│   │   ├── upload.py
│   │   └── web.py
│   ├── services
│   │   ├── analysis_service.py
│   │   ├── data_service.py
│   │   └── plot_service.py
│   ├── static
│   │   ├── css/style.css
│   │   └── js/app.js
│   ├── templates
│   │   └── index.html
│   └── utils
│       └── file_utils.py
├── data/uploads
├── plots
├── requirements.txt
└── scripts/init_db.py
```

## 3. 运行方式

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.init_db
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

服务启动后访问：

- 前端首页: <http://127.0.0.1:8001/>
- Swagger: <http://127.0.0.1:8001/docs>
- 健康检查: <http://127.0.0.1:8001/health>

使用独立页面 `Plot Bunny.html` 时，请先启动后端（默认 `http://127.0.0.1:8001`）。

## 4. API 列表

- `POST /datasets/excel/sheets`：识别 Excel 的 sheet 列表（`form-data`: `file`）
- `POST /datasets/preview`：预览当前文件当前sheet前12行（`form-data`: `file`, `sheet_name` 可选）
- `POST /datasets/upload`：上传 CSV/XLSX（`form-data`: `name`, `file`, `sheet_name` 可选）
- `GET /datasets`：查询数据集列表
- `GET /analysis/{dataset_id}/stats`：查看基础统计
- `POST /analysis/{dataset_id}/plot/time-dual-axis?...`：生成时间双Y轴曲线图
  - 必选：`time_column`、`left_y_columns`（可重复传参）、`right_y_columns`（可重复传参）
  - 可选格式：`x_min`/`x_max`（时间起止，需同时传）、`x_dtick_hours`（时间主刻度间隔，小时）、`y_left_min`/`y_left_max`、`y_right_min`/`y_right_max`、`y_left_dtick`、`y_right_dtick`、`series_colors_json`（按列名指定颜色）
  - 图表由 Plotly 生成，支持悬浮、缩放、平移等交互

## 5. 前端页面功能

- 上传 CSV/XLSX 并实时显示结果
- 选择 XLSX 时自动识别 sheet，并可下拉选择指定 sheet 解析
- 预览当前文件当前sheet前12行数据
- 一键刷新数据集列表
- 输入数据集 ID 后查看统计结果
- 自选时间列/左右Y轴列，支持同一纵轴多列同时作图（如多条温度曲线）
- 「图表格式设置」可自定义时间轴/双 Y 轴范围与刻度间隔，以及按曲线逐条设色；支持「恢复默认格式」一键清空并恢复默认调色板

## 6. 下一步可扩展方向

- 增加 Parquet 解析器
- 增加异常值检测、时间序列分析等算法模块
- 接入对象存储（S3/OSS）与 PostgreSQL
- 增加权限认证（JWT）与多租户隔离
- 将当前原生页面升级为 React/Vue 前端工程
