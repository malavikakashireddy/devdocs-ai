# Validation evidence — 2026-10-26

All results below refer to the prepared review branch, not to the original main branch.

| Check | Actual result |
| --- | --- |
| Python 3.12.14 + SQLite 3.53.1 | Used locally |
| pytest (unit + FastAPI API) | **17 passed** |
| Coverage with `--cov=backend` | **84% statements**; CLI/error branches still have gaps |
| Ruff lint and format | Passed |
| Evaluation CLI | Executed: 6 authored documents / 6 chunks / 8 smoke queries; document-level Recall@5 = 1.0 on that fixture |
| Repeat evaluation | Tests confirm stable rankings and corpus hash |
| Corpus SHA-256 | `957c370a7664dd78722e4ab400d90890d4a2af17520fb56a6ae2530b847bc203` |
| qrels SHA-256 | `05557622ff8145d63780fa0b90a6b7b1420d7b8609580ec9bc70add68a7ea1c2` |
| Docker image/Compose | Prepared; **not run** (no Docker runtime) |
| Remote GitHub Actions | [Passed: run 40399960644](https://github.com/malavikakashireddy/devdocs-ai/actions/runs/40399960644) |
| Embeddings/vector search/RAG/frontend | **Not implemented** |
| 1,000 files / 5,000 chunks / 250 queries / 85% Recall@5 | **Not verified** |

The smoke-fixture score is not evidence of general retrieval quality or a substitute for the earlier resume claim. Its queries deliberately match six short authored documents. The run took roughly 3 ms for all eight searches on this tiny local fixture, which is not a meaningful throughput benchmark and is not advertised as one.

Tests exercise idempotent updates, invalid-replacement preservation, source traversal rejection, literal query safety, source references, API validation, persistence, corpus exclusions, multibyte byte limits, qrels validation, and recall deduplication. The local test stack emits a Starlette warning about the future httpx2 TestClient migration; tests still pass. No live LLM, embedding model, or external database was mocked and then described as implemented AI functionality.
