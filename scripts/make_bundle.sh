#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

mkdir -p "${DIST_DIR}"

ZIP_NAME="PlotBunny-bundle.zip"
ZIP_PATH="${DIST_DIR}/${ZIP_NAME}"

rm -f "${ZIP_PATH}"

cd "${ROOT_DIR}"

# 最小可运行/可打包集合：
# - app/ 代码与静态资源（含 favicon）
# - START_WINDOWS.bat Windows 双击启动脚本
# - run_app.py 启动入口
# - requirements.txt 依赖
# - Plot Bunny.html 独立页
# - packaging/windows/ Windows EXE 打包脚本（可选但建议一起分发）
# - DIST_README.md 分发说明
zip -r "${ZIP_PATH}" \
  app \
  packaging/windows \
  "Plot Bunny.html" \
  START_WINDOWS.bat \
  run_app.py \
  requirements.txt \
  DIST_README.md \
  -x "*.pyc" "__pycache__/*" ".venv/*" "data/*" "plots/*" "dist/*"

echo "Created: ${ZIP_PATH}"

