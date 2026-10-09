"""Versioned API router. All v1 routes mount here."""

from fastapi import APIRouter

from app.api.v1.health import router as health_router

router = APIRouter()
router.include_router(health_router)
