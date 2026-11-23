"""Create the project directory structure per the implementation plan (T001).

Creates all required directories under the project root and writes
``logs/init.log`` listing every directory that was created (or already
existed). Exits non-zero only on genuine filesystem errors.
"""
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DIRECTORIES = [
    "code",
    "code/ingestion",
    "code/modeling",
    "code/analysis",
    "code/utils",
    "code/execution",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/validation",
    "data/models",
    "data/processing",
    "data/splits",
    "logs",
    "tests",
    "tests/unit",
    "tests/integration",
    "state/projects",
]

def create_structure() -> list:
    """Create all directories and return a list of (relpath, status)."""
    created = []
    for rel in DIRECTORIES:
        target = PROJECT_ROOT / rel
        if target.is_dir():
            created.append((rel, "exists"))
        else:
            target.mkdir(parents=True, exist_ok=True)
            created.append((rel, "created"))
    return created

def main() -> int:
    try:
        results = create_structure()
    except OSError:
        traceback.print_exc()
        return 1

    log_path = PROJECT_ROOT / "logs" / "init.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    lines = [
        f"# Project structure initialization ({timestamp})",
        f"project_root: {PROJECT_ROOT}",
    ]
    for rel, status in results:
        lines.append(f"{status}: {rel}")
    lines.append(f"total_directories: {len(results)}")
    lines.append(
        "created_count: %d" % sum(1 for _, s in results if s == "created")
    )
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path} ({len(results)} directories tracked)")
    return 0

if __name__ == "__main__":
    sys.exit(main())