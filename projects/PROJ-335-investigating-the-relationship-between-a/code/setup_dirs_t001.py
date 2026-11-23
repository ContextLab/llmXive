"""T001: Create the project directory structure per the implementation plan.

Creates (idempotently) the required directories:
code, data/raw, data/processed, data/metrics, data/results,
tests/unit, tests/integration, tests/contract, docs

After creation, verifies every directory exists and writes a manifest
of the created structure to data/results/structure_manifest.json as
concrete evidence that the structure is in place.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/metrics",
    "data/results",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "docs",
]

def create_project_structure() -> dict:
    """Create all required directories and return a status manifest."""
    root = paths.root
    created = []
    for rel in REQUIRED_DIRS:
        d = root / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
            log.info(f"Created directory: {rel}")
        else:
            log.info(f"Directory already exists: {rel}")

    missing = [rel for rel in REQUIRED_DIRS if not (root / rel).is_dir()]
    manifest = {
        "task": "T001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "required_directories": REQUIRED_DIRS,
        "created": created,
        "all_exist": not missing,
        "missing": missing,
    }
    if missing:
        log.error(f"Missing directories after creation: {missing}")
    return manifest

def main() -> None:
    manifest = create_project_structure()
    out = paths.data("results", "structure_manifest.json")
    with open(out, "w") as f:
        json.dump(manifest, f, indent=2)
    log.info(f"Structure manifest written to {out}")
    if not manifest["all_exist"]:
        raise SystemExit(1)
    log.info("T001 complete: project structure verified.")

if __name__ == "__main__":
    main()