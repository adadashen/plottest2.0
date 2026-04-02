import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DataPreviewResponse, DatasetResponse, ExcelSheetsResponse
from app.services.data_service import (
    get_excel_sheet_names,
    preview_tabular_file,
    save_and_parse_dataset,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetResponse)
def upload_dataset(
    name: str = Form(...),
    sheet_name: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    dataset = save_and_parse_dataset(db, name, file, sheet_name=sheet_name)
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        rows=dataset.rows,
        cols=dataset.cols,
        columns=json.loads(dataset.columns_json),
        created_at=dataset.created_at,
    )


@router.post("/excel/sheets", response_model=ExcelSheetsResponse)
def detect_excel_sheets(file: UploadFile = File(...)):
    sheets = get_excel_sheet_names(file)
    return ExcelSheetsResponse(file_name=file.filename or "", sheets=sheets)


@router.post("/preview", response_model=DataPreviewResponse)
def preview_dataset(
    file: UploadFile = File(...),
    sheet_name: str | None = Form(default=None),
):
    used_sheet, columns, rows, row_count = preview_tabular_file(
        file, sheet_name=sheet_name, limit=12
    )
    return DataPreviewResponse(
        file_name=file.filename or "",
        sheet_name=used_sheet,
        columns=columns,
        rows=rows,
        row_count=row_count,
    )
