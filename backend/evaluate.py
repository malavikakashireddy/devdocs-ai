"""Document-level macro Recall@k; relevance judgments must name existing sources."""

import argparse
import json
import platform
import sqlite3
import tempfile
import time
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from .app.retrieval import DocumentStore
from .ingest import ingest_directory


def recall_at_k(retrieved, relevant):
    if not relevant:
        raise ValueError("every query needs at least one relevant source")
    return len(set(retrieved) & set(relevant)) / len(set(relevant))


def evaluate(corpus: Path, qrels_path: Path, k: int):
    if not 1 <= k <= 20:
        raise ValueError("k must be 1–20")
    qrels = [json.loads(line) for line in qrels_path.read_text().splitlines() if line.strip()]
    if not qrels or len({q["id"] for q in qrels}) != len(qrels):
        raise ValueError("evaluation requires nonempty queries with unique IDs")
    with tempfile.TemporaryDirectory() as directory:
        store = DocumentStore(str(Path(directory) / "evaluation.sqlite3"))
        ingest_directory(store, corpus)
        with closing(store.connect()) as db:
            sources = {
                row["source"]: row["digest"] for row in db.execute("SELECT * FROM documents")
            }
        if not sources:
            raise ValueError("corpus is empty")
        results = []
        started = time.perf_counter()
        for q in qrels:
            if not q["relevant_sources"] or set(q["relevant_sources"]) - sources.keys():
                raise ValueError("qrels reference missing sources or contain no judgments")
            if not q["query"].strip():
                raise ValueError("query must contain text")
            retrieved = [hit["source"] for hit in store.search(q["query"], k)]
            results.append(
                {
                    "id": q["id"],
                    "retrieved": retrieved,
                    "recall": recall_at_k(retrieved, q["relevant_sources"]),
                }
            )
        elapsed = time.perf_counter() - started
        return {
            "retriever": "sqlite-fts5-bm25",
            "metric": "document-level macro Recall@k",
            "k": k,
            "queries": len(qrels),
            **store.stats(),
            "recall": sum(q["recall"] for q in results) / len(results),
            "corpus_sha256": sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest(),
            "qrels_sha256": sha256(qrels_path.read_bytes()).hexdigest(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
            "search_seconds": elapsed,
            "per_query": results,
            "scope": "Small authored smoke fixture; not the claimed 250-query benchmark.",
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("evaluation/corpus"))
    parser.add_argument("--qrels", type=Path, default=Path("evaluation/queries.jsonl"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(evaluate(args.corpus, args.qrels, args.k), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n")
    print(result)


if __name__ == "__main__":
    main()
