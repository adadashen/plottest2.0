from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import Base, engine
from app.routers import analysis, datasets, upload, web

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Plot Bunny", version="0.1.0")

# 允许独立页面(file://)和本地开发页面跨域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.environ.get("APP_STATIC_DIR", "app/static")), name="static")
app.mount("/plots", StaticFiles(directory="plots"), name="plots")

app.include_router(web.router)
app.include_router(upload.router)
app.include_router(datasets.router)
app.include_router(analysis.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
