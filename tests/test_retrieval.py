from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.retrieval import DocumentStore, chunk_document
from backend.evaluate import evaluate, recall_at_k
from backend.ingest import ingest_directory


@pytest.fixture
def store(tmp_path):
    return DocumentStore(str(tmp_path / "index.sqlite3"))


def test_chunk_provenance_and_overlap():
    chunks = list(chunk_document("\n".join(f"line {i}" for i in range(61))))
    assert [(start, end) for start, end, _ in chunks] == [(1, 30), (26, 55), (51, 61)]
    assert chunks[1][2].splitlines()[0] == "line 25"


def test_idempotent_ingestion_and_atomic_replacement(store):
    assert store.ingest("docs/api.md", "FastAPI validation")["changed"]
    assert not store.ingest("docs/api.md", "FastAPI validation")["changed"]
    store.ingest("docs/api.md", "Kafka offsets")
    assert store.stats() == {"documents": 1, "chunks": 1}
    assert not store.search("validation")
    assert store.search("Kafka")[0]["source"] == "docs/api.md"
    with pytest.raises(ValueError):
        store.ingest("docs/api.md", " ")
    assert store.search("Kafka")  # bad replacement leaves prior data intact


@pytest.mark.parametrize(
    "source",
    ["../key.md", "/etc/passwd", ".env", ".git/config", "docs/../file.md", "keys.pem", "a\\b.md"],
)
def test_reject_unsafe_sources(store, source):
    with pytest.raises(ValueError):
        store.ingest(source, "not indexed")
    assert store.stats()["documents"] == 0


def test_query_operators_are_literal_and_sql_is_parameterized(store):
    store.ingest("a.md", "Kafka pipeline")
    assert store.search('Kafka"; DROP TABLE documents; --')
    assert store.stats()["documents"] == 1
    assert store.search('*** : "') == []


def test_persistent_reopen_and_empty_search(store):
    store.ingest("a.md", "PostgreSQL pooling")
    assert DocumentStore(store.path).search("pooling")
    assert not store.search("nonexistent")


def test_directory_skips_hidden_symlink_and_binary(tmp_path, store):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "safe.md").write_text("safe text")
    (corpus / ".env").write_text("secret")
    (corpus / "binary.md").write_bytes(b"\xff\xfe")
    (corpus / "link.md").symlink_to(corpus / "safe.md")
    report = ingest_directory(store, corpus)
    assert report == {"indexed": 1, "unchanged": 0, "skipped": 2}
    assert ingest_directory(store, corpus)["unchanged"] == 1


def test_api_validation_and_source_references(tmp_path):
    with TestClient(create_app(str(tmp_path / "api.sqlite3"))) as client:
        assert client.get("/").status_code == 200
        assert client.get("/health").json()["documents"] == 0
        result = client.post("/documents", json={"source": "docs/a.md", "text": "Kafka offsets"})
        assert result.status_code == 201
        hit = client.get("/search", params={"query": "Kafka"}).json()["results"][0]
        assert (hit["source"], hit["start_line"], hit["end_line"]) == ("docs/a.md", 1, 1)
        for params in [{"query": "x", "k": 21}, {"query": ""}, {"query": "x" * 501}]:
            assert client.get("/search", params=params).status_code == 422
        assert client.post("/documents", json={"source": "a.md", "text": " "}).status_code == 422
        assert client.post("/documents", json={"source": ".env", "text": "x"}).status_code == 422


def test_multibyte_document_limit(store):
    with pytest.raises(ValueError):
        store.ingest("large.md", "é" * 500001)


def test_recall_deduplicates_sources_and_counts_misses():
    assert recall_at_k(["a", "a", "c"], ["a", "b"]) == 0.5
    assert recall_at_k([], ["a"]) == 0
    with pytest.raises(ValueError):
        recall_at_k([], [])


def test_evaluation_is_reproducible():
    first = evaluate(Path("evaluation/corpus"), Path("evaluation/queries.jsonl"), 5)
    second = evaluate(Path("evaluation/corpus"), Path("evaluation/queries.jsonl"), 5)
    assert first["queries"] == 8 and first["documents"] == 6
    assert first["corpus_sha256"] == second["corpus_sha256"]
    assert first["per_query"] == second["per_query"]


def test_bad_qrels_are_rejected(tmp_path):
    qrels = tmp_path / "bad.jsonl"
    qrels.write_text('{"id":"q","query":"x","relevant_sources":["missing.md"]}\n')
    with pytest.raises(ValueError):
        evaluate(Path("evaluation/corpus"), qrels, 5)
