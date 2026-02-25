"""FastAPI application entry-point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.controllers.ticket_controller import router as ticket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the data/ directory exists for SQLite
    os.makedirs("data", exist_ok=True)
    await init_db()
    yield


app = FastAPI(
    title="AI Ticket Triage API",
    version="1.0.0",
    description="Heuristic-based support ticket classification and prioritization.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS – allow the Vite dev server and the nginx-fronted production build
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # alternative dev port
        "http://localhost",        # nginx in Docker
        "http://localhost:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ticket_router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok"}
