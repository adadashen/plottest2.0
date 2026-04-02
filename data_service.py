import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models import Dataset
from app.utils.file_utils import build_uploaded_file_path

UPLOAD_DIR = "data/uploads"
SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def _read_tabular_file(file_path: str, ext: str, sheet_name: str | None = None) -> pd.DataFrame:
    if ext == ".csv":
        return pd.read_csv(file_path)
    if ext == ".xlsx":
        if sheet_name:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        return pd.read_excel(file_path, sheet_name=0)
    raise ValueError(f"不支持的文件类型: {ext}")


def _json_safe_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def preview_tabular_file(
    file: UploadFile, sheet_name: str | None = None, limit: int = 12
) -> tuple[str | None, list[str], list[dict[str, Any]], int]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="上传文件必须包含文件名")
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="当前仅支持 CSV 或 XLSX 文件")

    try:
        if ext == ".csv":
            df = pd.read_csv(file.file)
            used_sheet_name = None
        else:
            excel = pd.ExcelFile(file.file)
            chosen_sheet = sheet_name or excel.sheet_names[0]
            if chosen_sheet not in excel.sheet_names:
                raise HTTPException(status_code=400, detail=f"sheet 不存在: {chosen_sheet}")
            df = pd.read_excel(excel, sheet_name=chosen_sheet)
            used_sheet_name = chosen_sheet

        preview_df = df.head(limit)
        columns = [str(col) for col in preview_df.columns.tolist()]
        records = [
            {str(key): _json_safe_value(value) for key, value in row.items()}
            for row in preview_df.to_dict(orient="records")
        ]
        return used_sheet_name, columns, records, int(len(df))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"文件预览失败: {exc}") from exc
    finally:
        file.file.close()


def get_excel_sheet_names(file: UploadFile) -> list[str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="上传文件必须包含文件名")
    ext = Path(file.filename).suffix.lower()
    if ext != ".xlsx":
        raise HTTPException(status_code=400, detail="仅支持 XLSX 文件识别 sheet")

    try:
        excel = pd.ExcelFile(file.file)
        return list(excel.sheet_names)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"读取 Excel sheet 失败: {exc}") from exc
    finally:
        file.file.close()


def save_and_parse_dataset(
    db: Session, name: str, file: UploadFile, sheet_name: str | None = None
) -> Dataset:
    if not file.filename:
        raise HTTPException(status_code=400, detail="上传文件必须包含文件名")
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="当前仅支持 CSV 或 XLSX 文件")
    if ext == ".csv" and sheet_name:
        raise HTTPException(status_code=400, detail="CSV 文件不支持 sheet_name 参数")

    target_path = build_uploaded_file_path(file.filename, UPLOAD_DIR)

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        df = _read_tabular_file(target_path, ext, sheet_name=sheet_name)
    except Exception as exc:
        if Path(target_path).exists():
            Path(target_path).unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"文件解析失败: {exc}") from exc
    finally:
        file.file.close()

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
    return dataset


def get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return dataset


def list_datasets(db: Session) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()
