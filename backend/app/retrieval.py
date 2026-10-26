"""Persistent lexical retrieval baseline with line-level source provenance."""

import re
import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import PurePosixPath

MAX_DOCUMENT_BYTES = 1_000_000
MAX_LINE_CHARACTERS = 10_000


def validate_source(source: str) -> str:
    path = PurePosixPath(source)
    if (
        not source.strip()
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in source
        or any(part.startswith(".") for part in path.parts)
    ):
        raise ValueError("source must be a relative, non-hidden path without traversal")
    if path.name.lower().startswith("env") or path.suffix.lower() in {".pem", ".key"}:
        raise ValueError("credential files cannot be indexed")
    return source


def chunk_document(text: str, lines_per_chunk: int = 30, overlap: int = 5):
    if not 0 <= overlap < lines_per_chunk:
        raise ValueError("overlap must be smaller than lines_per_chunk")
    if not text.strip() or len(text.encode("utf-8")) > MAX_DOCUMENT_BYTES:
        raise ValueError("document must contain text and fit within 1 MB")
    lines = text.splitlines()
    if any(len(line) > MAX_LINE_CHARACTERS for line in lines):
        raise ValueError("line exceeds 10,000 characters; reformat before indexing")
    for start in range(0, len(lines), lines_per_chunk - overlap):
        end = min(start + lines_per_chunk, len(lines))
        content = "\n".join(lines[start:end])
        if content.strip():
            yield start + 1, end, content
        if end == len(lines):
            break


class DocumentStore:
    def __init__(self, path: str):
        self.path = path
        with closing(self.connect()) as db, db:
            db.execute("""CREATE TABLE IF NOT EXISTS documents (
                source TEXT PRIMARY KEY, digest TEXT NOT NULL)""")
            db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
                source UNINDEXED, start_line UNINDEXED, end_line UNINDEXED,
                content, tokenize='unicode61')""")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def ingest(self, source: str, text: str) -> dict:
        validate_source(source)
        chunks = list(chunk_document(text))
        digest = sha256(text.encode("utf-8")).hexdigest()
        with closing(self.connect()) as db, db:
            old = db.execute("SELECT digest FROM documents WHERE source = ?", (source,)).fetchone()
            if old and old["digest"] == digest:
                return {"source": source, "chunks": len(chunks), "changed": False, "sha256": digest}
            db.execute("DELETE FROM chunks WHERE source = ?", (source,))
            db.executemany(
                "INSERT INTO chunks VALUES (?, ?, ?, ?)",
                [(source, start, end, content) for start, end, content in chunks],
            )
            db.execute(
                "INSERT INTO documents VALUES (?, ?) ON CONFLICT(source) DO UPDATE SET digest=excluded.digest",
                (source, digest),
            )
        return {"source": source, "chunks": len(chunks), "changed": True, "sha256": digest}

    def search(self, query: str, k: int = 5) -> list[dict]:
        if not 1 <= k <= 20 or not 1 <= len(query) <= 500:
            raise ValueError("query length must be 1–500 and k must be 1–20")
        # Quote each token: users cannot submit FTS operators or SQL fragments.
        tokens = re.findall(r"[^\W_]+", query, re.UNICODE)
        if not tokens:
            return []
        match = " OR ".join('"' + token + '"' for token in dict.fromkeys(tokens))
        with closing(self.connect()) as db:
            rows = db.execute(
                """SELECT source, start_line, end_line, content,
                bm25(chunks) AS score FROM chunks WHERE chunks MATCH ?
                ORDER BY score, source, CAST(start_line AS INTEGER) LIMIT ?""",
                (match, k),
            ).fetchall()
        return [dict(row) for row in rows]

    def stats(self) -> dict:
        with closing(self.connect()) as db:
            return {
                "documents": db.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
                "chunks": db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
            }
