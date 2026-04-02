import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

import webview

from app.database import SessionLocal
from app.models import Dataset
from app.services.analysis_service import compute_basic_stats, load_dataframe
from app.services.plot_service import generate_dual_axis_line_plot
from app.utils.file_utils import build_uploaded_file_path


UPLOAD_DIR = "data/uploads"


def _json_safe_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _read_tabular_file(file_path: str, sheet_name: str | None = None) -> tuple[pd.DataFrame, str | None]:
    p = Path(file_path)
    ext = p.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(file_path), None
    if ext == ".xlsx":
        excel = pd.ExcelFile(file_path)
        chosen = sheet_name or excel.sheet_names[0]
        if chosen not in excel.sheet_names:
            raise ValueError(f"sheet 不存在: {chosen}")
        return pd.read_excel(excel, sheet_name=chosen), chosen
    raise ValueError("当前仅支持 CSV 或 XLSX 文件")


class DesktopAPI:
    """
    pywebview JS API：前端通过 window.pywebview.api 调用这里的方法。
    所有方法返回 JSON 友好的 dict/list。
    """

    def __init__(self, window=None):
        self._window = window

    # ---------- File dialog ----------
    def pick_file(self) -> str | None:
        if not self._window:
            return None
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Data (*.csv;*.xlsx)",),
        )
        if not result:
            return None
        return str(result[0])

    # ---------- Excel sheets / preview ----------
    def excel_sheets(self, file_path: str) -> dict:
        p = Path(file_path)
        if p.suffix.lower() != ".xlsx":
            return {"file_name": p.name, "sheets": []}
        excel = pd.ExcelFile(str(p))
        return {"file_name": p.name, "sheets": list(excel.sheet_names)}

    def preview_file(self, file_path: str, sheet_name: str | None = None, limit: int = 12) -> dict:
        df, used_sheet = _read_tabular_file(file_path, sheet_name=sheet_name)
        preview_df = df.head(limit)
        columns = [str(c) for c in preview_df.columns.tolist()]
        rows = [
            {str(k): _json_safe_value(v) for k, v in row.items()}
            for row in preview_df.to_dict(orient="records")
        ]
        return {
            "file_name": Path(file_path).name,
            "sheet_name": used_sheet,
            "columns": columns,
            "rows": rows,
            "row_count": int(len(df)),
        }

    # ---------- Dataset CRUD ----------
    def list_datasets(self) -> list[dict]:
        with SessionLocal() as db:
            items = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
            out = []
            for it in items:
                out.append(
                    {
                        "id": it.id,
                        "name": it.name,
                        "rows": it.rows,
                        "cols": it.cols,
                        "columns": json.loads(it.columns_json),
                        "created_at": it.created_at.isoformat() if hasattr(it.created_at, "isoformat") else str(it.created_at),
                    }
                )
            return out

    def upload_dataset(self, name: str, file_path: str, sheet_name: str | None = None) -> dict:
        src = Path(file_path)
        if not src.exists():
            raise ValueError(f"文件不存在: {file_path}")
        ext = src.suffix.lower()
        if ext not in {".csv", ".xlsx"}:
            raise ValueError("当前仅支持 CSV 或 XLSX 文件")
        if ext == ".csv" and sheet_name:
            raise ValueError("CSV 文件不支持 sheet_name")

        Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        target_path = build_uploaded_file_path(src.name, UPLOAD_DIR)
        shutil.copyfile(str(src), target_path)

        df, _ = _read_tabular_file(target_path, sheet_name=sheet_name)

        with SessionLocal() as db:
            dataset = Dataset(
                name=name,
                file_path=target_path,
                rows=int(df.shape[0]),
                cols=int(df.shape[1]),
                columns_json=json.dumps(df.columns.tolist(), ensure_ascii=False),
            )
            db.add(dataset)
            db.commit()
            db.refresh(dataset)
            return {
                "id": dataset.id,
                "name": dataset.name,
                "rows": dataset.rows,
                "cols": dataset.cols,
                "columns": json.loads(dataset.columns_json),
                "created_at": dataset.created_at.isoformat() if hasattr(dataset.created_at, "isoformat") else str(dataset.created_at),
            }

    # ---------- Stats / Plot ----------
    def stats(self, dataset_id: int) -> dict:
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError("数据集不存在")
            df = load_dataframe(dataset)
            numeric_columns, describe = compute_basic_stats(df)
            return {"dataset_id": dataset.id, "numeric_columns": numeric_columns, "describe": describe}

    def plot_time_dual_axis(self, dataset_id: int, params: dict) -> dict:
        with SessionLocal() as db:
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise ValueError("数据集不存在")
            df = load_dataframe(dataset)

        output_path = generate_dual_axis_line_plot(
            df,
            dataset_id,
            time_column=params["time_column"],
            left_y_columns=params["left_y_columns"],
            right_y_columns=params["right_y_columns"],
            x_min=params.get("x_min"),
            x_max=params.get("x_max"),
            y_left_min=params.get("y_left_min"),
            y_left_max=params.get("y_left_max"),
            y_right_min=params.get("y_right_min"),
            y_right_max=params.get("y_right_max"),
            x_dtick_hours=params.get("x_dtick_hours"),
            y_left_dtick=params.get("y_left_dtick"),
            y_right_dtick=params.get("y_right_dtick"),
            chart_title=params.get("chart_title"),
            x_title=params.get("x_title"),
            y_left_title=params.get("y_left_title"),
            y_right_title=params.get("y_right_title"),
            series_colors_json=params.get("series_colors_json"),
        )

        html = Path(output_path).read_text(encoding="utf-8", errors="ignore")
        return {"output_path": output_path, "html": html}

