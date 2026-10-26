# Engineering roadmap

1. **Corpus provenance:** select a redistributable documentation corpus; record upstream revisions, licenses, file counts, chunk counts, and exclusions. Do not ingest private employer code.
2. **Semantic retrieval:** introduce a retriever interface and a local embedding model or explicit provider adapter. Pin model/version/dimensions; cache embeddings by content hash; retain lexical BM25 as a baseline. Add pgvector only when persistence/concurrency requirements justify it.
3. **Evaluation:** author and independently review 250 query judgments if that scope is still desired. Separate development and held-out queries, include paraphrases and unanswerable questions, and report Recall@1/5/10, MRR, latency, corpus hashes, hardware, and failure cases. Never tune on held-out labels.
4. **Hybrid retrieval:** compare rank fusion and reranking against each baseline using the same queries. Publish per-query results and ablations; avoid reporting a single unexplained percentage.
5. **Grounded answers:** add an optional LLM adapter with source citations, explicit insufficient-context behavior, prompt-injection boundaries, token budgets, timeout/retry limits, and cost tracing. Evaluate citation support separately from retrieval.
6. **Frontend and operations:** build search/result navigation first; then streaming answers. Add authentication, migrations, upload body limits, retention/deletion, structured telemetry, and load tests before public hosting.

Acceptance evidence should be committed alongside each feature. The original large-corpus numbers remain unverified; reaching similar numbers later does not validate an earlier claim.
