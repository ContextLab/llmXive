"""Task T001: verify the required project directory layout exists.

Creates every directory required by the project plan (idempotent) and
verifies each one exists on disk, printing a recursive listing of the
``code/`` tree plus the specs contracts directory. Exits 0 when the full
layout is present, 1 otherwise.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths

ROOT = paths.root

REQUIRED_DIRS = [
    "code/src/config",
    "code/src/extraction",
    "code/src/detection",
    "code/src/inference",
    "code/src/analysis",
    "code/src/reporting",
    "code/src/pipeline",
    "code/src/cli",
    "code/tests/unit",
    "code/tests/integration",
    "code/tests/contract",
    "code/data/raw",
    "code/data/annotations",
    "code/data/derived",
    "code/data/results",
    "code/logs",
    "specs/001-evaluating-the-impact-of-code-generation/contracts",
]


def main() -> int:
    missing = []
    for rel in REQUIRED_DIRS:
        d = ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        if not d.is_dir():
            missing.append(rel)

    if missing:
        print("MISSING DIRECTORIES: " + ", ".join(missing), file=sys.stderr)
        return 1

    print("All required directories exist:")
    for rel in REQUIRED_DIRS:
        print(f"  OK  {rel}")

    print("\nRecursive listing of code/:")
    for p in sorted((ROOT / "code").rglob("*")):
        if p.is_dir():
            print(f"  {p.relative_to(ROOT)}/")
    contracts = ROOT / "specs/001-evaluating-the-impact-of-code-generation/contracts"
    print(f"  {contracts.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())