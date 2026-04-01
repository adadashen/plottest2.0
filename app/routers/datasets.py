import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DatasetResponse
from app.services.data_service import list_datasets

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[DatasetResponse])
def get_datasets(db: Session = Depends(get_db)):
    items = list_datasets(db)
    return [
        DatasetResponse(
            id=item.id,
            name=item.name,
            rows=item.rows,
            cols=item.cols,
            columns=json.loads(item.columns_json),
            created_at=item.created_at,
        )
        for item in items
    ]
