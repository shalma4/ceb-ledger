import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy.exc import OperationalError

from app.api.routes import health, transactions, reconciliation, exceptions
from app.core.config import settings
from app.db.session import engine, Base
import app.models.transaction
import app.models.reconciliation
import app.models.exception
import app.models.idempotency


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry database connection on startup to handle container network initialization
    retries = 10
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            print("Database connected and schema initialized successfully.")
            break
        except OperationalError as e:
            retries -= 1
            print(f"Waiting for database connection... ({retries} retries left)")
            time.sleep(2)
            if retries == 0:
                raise e
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Financial transaction and reconciliation simulation backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Base routes
app.include_router(health.router)

# API v1 routes
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(reconciliation.router, prefix=settings.API_V1_STR)
app.include_router(exceptions.router, prefix=settings.API_V1_STR)
