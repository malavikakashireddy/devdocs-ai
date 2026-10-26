"""Index an explicit local corpus, never remote URLs or arbitrary server paths."""

import argparse
import json
from pathlib import Path

from .app.retrieval import MAX_DOCUMENT_BYTES, DocumentStore

EXTENSIONS = {".md", ".txt", ".py", ".go", ".java", ".c", ".h", ".cpp", ".ts", ".tsx"}
EXCLUDED = {"node_modules", "vendor", "dist", "build", "venv", "__pycache__"}


def ingest_directory(store, root):
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("corpus must be a directory")
    report = {"indexed": 0, "unchanged": 0, "skipped": 0}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (
            any(x.startswith(".") or x in EXCLUDED for x in relative.parts)
            or path.suffix.lower() not in EXTENSIONS
        ):
            continue
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            report["skipped"] += 1
            continue
        if not path.is_file() or path.stat().st_size > MAX_DOCUMENT_BYTES:
            report["skipped"] += 1
            continue
        try:
            result = store.ingest(relative.as_posix(), path.read_text(encoding="utf-8"))
        except (UnicodeError, ValueError):
            report["skipped"] += 1
            continue
        report["indexed" if result["changed"] else "unchanged"] += 1
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path)
    parser.add_argument("--db", default=".data/devdocs.sqlite3")
    args = parser.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    store = DocumentStore(args.db)
    print(json.dumps({**ingest_directory(store, args.corpus), **store.stats()}, indent=2))


if __name__ == "__main__":
    main()
