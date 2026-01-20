from fastapi import FastAPI
from contextlib import asynccontextmanager
import os

from src.core.database import SessionLocal
from src.models.system_setting import SystemSetting


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # Startup
    db = SessionLocal()
    try:
        SystemSetting.init_config(db)
        print("✓ System settings initialized")
    finally:
        db.close()

    yield

    # Shutdown
    print("✓ Application shutting down")


app = FastAPI(
    title="CIS Handmade API",
    description="CIS 관리 시스템 API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "CIS Handmade API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# 라우터 추가 예시
# from src.api.v1 import users, events, groups
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
# app.include_router(groups.router, prefix="/api/v1/groups", tags=["groups"])
