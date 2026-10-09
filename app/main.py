"""Application factory — the only place a FastAPI instance is created.

Why a `create_app()` factory instead of `app = FastAPI()` at import time?
- Tests can build isolated app instances.
- Lifespan (startup/shutdown) logic stays explicit and testable.
- Config/logging are applied once, before routes mount.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup: Step 3 will start the MQTT worker here.
    logger = logging.getLogger(__name__)
    logger.info("startup complete")
    yield
    # Shutdown: Step 1 will dispose the DB engine here.
    logger.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(v1_router, prefix=settings.api_v1_prefix)
    return app


# Uvicorn entrypoint: `uvicorn app.main:app --reload`
app = create_app()
