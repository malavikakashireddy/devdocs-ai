# DevDocs AI

AI-powered developer documentation and codebase intelligence platform.

## Overview

DevDocs AI helps developers understand unfamiliar codebases and technical documentation by combining document ingestion, semantic search, and AI-generated answers.

## Current Status

🚧 Version 0.1 — Initial backend implementation

The current version provides a FastAPI backend with health-check and API endpoints. Retrieval, embeddings, PostgreSQL/pgvector, and the frontend will be added incrementally.

## Tech Stack

* Python
* FastAPI
* PostgreSQL
* pgvector
* React
* Docker
* LLMs and embeddings

## Architecture

```text
Developer
    │
    ▼
React Frontend
    │
    ▼
FastAPI Backend
    │
    ├── Document Ingestion
    │
    ├── Embeddings
    │
    ├── Semantic / Hybrid Search
    │
    ▼
PostgreSQL + pgvector
    │
    ▼
LLM
    │
    ▼
Source-Grounded Answer
```

## Current API

### Health Check

```text
GET /health
```

Returns:

```json
{
  "status": "healthy"
}
```

### API Documentation

When running locally:

```text
http://127.0.0.1:8000/docs
```

## Running Locally

Clone the repository:

```bash
git clone https://github.com/malavikakashireddy/devdocs-ai.git
cd devdocs-ai
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Start the API:

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Roadmap

* [x] FastAPI backend
* [x] Health-check endpoint
* [ ] Document ingestion
* [ ] PostgreSQL integration
* [ ] pgvector embeddings
* [ ] Semantic search
* [ ] Retrieval-Augmented Generation (RAG)
* [ ] Code parsing and code intelligence
* [ ] Hybrid search
* [ ] Reranking
* [ ] Retrieval evaluation
* [ ] React frontend
* [ ] Dockerized deployment
* [ ] CI/CD
* [ ] Observability and performance benchmarking

## Goal

Build a production-oriented AI developer tool that can understand large codebases and technical documentation while providing answers grounded in the underlying source files.
