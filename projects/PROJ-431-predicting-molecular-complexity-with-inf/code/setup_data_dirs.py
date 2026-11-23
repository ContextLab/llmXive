"""T009: Create the project data/results directory structure.

Creates (idempotently) the directories required by the pipeline:
data/raw, data/processed, results/models, results/reports, results/plots,
plus code/ and tests/ scaffolding directories, and writes a manifest
listing the created paths to results/reports/directory_manifest.json as
evidence that the hierarchy exists.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "data/raw",
    "data/processed",
    "results/models",
    "results/reports",
    "results/plots",
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
]


def main() -> int:
    created = []
    existing = []
    for rel in DIRECTORIES:
        d = paths.path(*rel.split("/"))
        if d.exists():
            existing.append(str(d))
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
    # Add .gitkeep files so empty dirs persist in version control.
    for rel in DIRECTORIES:
        keep = paths.path(*rel.split("/")) / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

    manifest = {
        "task": "T009",
        "directories": [str(paths.path(*rel.split("/"))) for rel in DIRECTORIES],
        "created_now": created,
        "already_existing": existing,
    }
    out = paths.results("reports", "directory_manifest.json")
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Directory structure verified:")
    for rel in DIRECTORIES:
        print(f"  {rel}/ -> {paths.path(*rel.split('/'))}")
    print(f"Manifest written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())