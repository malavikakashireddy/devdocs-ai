import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field, field_validator

from .retrieval import MAX_DOCUMENT_BYTES, DocumentStore, validate_source

logger = logging.getLogger(__name__)


class Document(BaseModel):
    source: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=MAX_DOCUMENT_BYTES)

    @field_validator("source")
    @classmethod
    def source_is_safe(cls, value):
        return validate_source(value)


def create_app(db_path: str | None = None):
    @asynccontextmanager
    async def lifespan(app):
        path = db_path or os.getenv("DEVDOCS_DB_PATH", ".data/devdocs.sqlite3")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        app.state.store = DocumentStore(path)
        yield

    api = FastAPI(
        title="DevDocs AI",
        version="0.2.0",
        description="Document ingestion and lexical retrieval baseline. Embeddings and RAG are planned.",
        lifespan=lifespan,
    )

    @api.exception_handler(sqlite3.Error)
    async def storage_error(request, exc):
        # Never return database paths or raw query/input data in errors.
        logger.error("document store unavailable: %s", type(exc).__name__)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"detail": "Document store unavailable"})

    @api.get("/")
    def root():
        return {"message": "DevDocs AI API is running", "version": "0.2.0"}

    @api.get("/health")
    def health_check(request: Request):
        return {"status": "healthy", **request.app.state.store.stats()}

    @api.post("/documents", status_code=201)
    def ingest_document(document: Document, request: Request):
        try:
            return request.app.state.store.ingest(document.source, document.text)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @api.get("/search")
    def search(
        request: Request,
        query: str = Query(min_length=1, max_length=500),
        k: int = Query(default=5, ge=1, le=20),
    ):
        return {
            "retriever": "sqlite-fts5-bm25",
            "results": request.app.state.store.search(query, k),
        }

    return api


app = create_app()
