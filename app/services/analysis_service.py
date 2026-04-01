import json

import pandas as pd
from fastapi import HTTPException

from app.models import Dataset


def load_dataframe(dataset: Dataset) -> pd.DataFrame:
    file_path = dataset.file_path.lower()
    if file_path.endswith(".csv"):
        return pd.read_csv(dataset.file_path)
    if file_path.endswith(".xlsx"):
        # 上传 XLSX 时用户可能选择了非首个 sheet。这里根据保存的列结构回溯到匹配 sheet，
        # 避免后续统计/作图误读到第一个 sheet 导致“列不存在”。
        expected_columns = json.loads(dataset.columns_json or "[]")
        if not expected_columns:
            return pd.read_excel(dataset.file_path, sheet_name=0)
        excel = pd.ExcelFile(dataset.file_path)
        for sheet in excel.sheet_names:
            sheet_df = pd.read_excel(excel, sheet_name=sheet)
            if sheet_df.columns.tolist() == expected_columns:
                return sheet_df
        return pd.read_excel(excel, sheet_name=0)
    raise HTTPException(status_code=400, detail="不支持的数据集文件类型")


def compute_basic_stats(df: pd.DataFrame) -> tuple[list[str], dict]:
    numeric_df = df.select_dtypes(include="number")
    numeric_columns = numeric_df.columns.tolist()
    describe = numeric_df.describe().fillna(0).to_dict() if not numeric_df.empty else {}
    return numeric_columns, describe


def compute_correlation(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {}
    corr_df = numeric_df.corr().fillna(0)
    return {
        col: {inner_col: float(value) for inner_col, value in row.items()}
        for col, row in corr_df.to_dict().items()
    }
