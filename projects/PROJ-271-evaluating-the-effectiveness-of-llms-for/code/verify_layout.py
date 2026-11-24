"""Verify the project directory layout required by task T005.

Imports the ``code`` package (which creates the directories at import
time), then checks that ``data/raw``, ``data/processed`` and ``results``
exist on disk. Writes the evidence to ``results/layout_verification.json``
and exits non-zero if any required directory is missing.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Importing the package triggers directory creation (idempotent).
import code  # noqa: E402  (import after sys.path setup)

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "results",
    "tests/unit",
    "tests/contract",
]

def main() -> int:
    results_dir = PROJECT_ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    checks = {}
    all_ok = True
    for rel in REQUIRED_DIRS:
        path = PROJECT_ROOT / rel
        exists = path.is_dir()
        checks[rel] = {
            "exists": exists,
            "absolute_path": str(path),
        }
        if not exists:
            all_ok = False
            print(f"MISSING directory: {rel}", file=sys.stderr)

    report = {
        "task_id": "T005",
        "package_imported": True,
        "package_root": str(code.PROJECT_ROOT),
        "directories": checks,
        "all_present": all_ok,
    }

    output_path = results_dir / "layout_verification.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Layout verification written to {output_path}")
    print(f"all_present: {all_ok}")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
