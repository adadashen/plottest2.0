from datetime import datetime
from typing import Any

from pydantic import BaseModel


class DatasetBase(BaseModel):
    name: str


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    id: int
    rows: int
    cols: int
    columns: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ExcelSheetsResponse(BaseModel):
    file_name: str
    sheets: list[str]


class DataPreviewResponse(BaseModel):
    file_name: str
    sheet_name: str | None = None
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int


class BasicStatsResponse(BaseModel):
    dataset_id: int
    numeric_columns: list[str]
    describe: dict[str, Any]


class PlotResponse(BaseModel):
    dataset_id: int
    plot_type: str
    output_path: str
