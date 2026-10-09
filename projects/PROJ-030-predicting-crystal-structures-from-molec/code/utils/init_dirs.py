"""
T001-recovery / T001b: Initialize the full project directory tree.

Creates every data/logs directory required by the pipeline (CPU-only
environment, no CUDA cache dirs) and writes a confirmation marker to
``data/.initialized``. Exits 0 on success.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DIRECTORIES = [
    "data",
    "data/raw",
    "data/processed",
    "data/processing",
    "data/results",
    "data/validation",
    "data/models",
    "data/splits",
    "logs",
    "state/projects",
    "code",
    "code/utils",
    "code/ingestion",
    "code/modeling",
    "code/analysis",
    "tests/unit",
    "tests/integration",
]


def init_directories(root: Path = PROJECT_ROOT) -> Path:
    """Create the full directory tree and write ``data/.initialized``.

    Args:
        root: Project root directory (defaults to this file's project).

    Returns:
        Path to the ``data/.initialized`` marker file.
    """
    created = []
    for rel in DIRECTORIES:
        d = root / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)

    marker = root / "data" / ".initialized"
    marker.write_text(
        json.dumps(
            {
                "initialized_at": datetime.now(timezone.utc).isoformat(),
                "project_root": str(root),
                "directories": DIRECTORIES,
                "created_now": created,
                "environment": "cpu-only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return marker


def main() -> int:
    marker = init_directories()
    print(f"Directory tree initialized. Marker written to {marker}")
    return 0


if __name__ == "__main__":
    sys.exit(main())