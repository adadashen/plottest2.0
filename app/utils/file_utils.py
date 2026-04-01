import os
import uuid
from pathlib import Path


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def build_uploaded_file_path(original_name: str, upload_dir: str) -> str:
    ensure_dir(upload_dir)
    ext = Path(original_name).suffix or ".csv"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(upload_dir, unique_name)
