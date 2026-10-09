"""
create_project_structure.py
---------------------------
This script creates the required project directory structure for
**PROJ-175-statistical-analysis-of-publicly-availab** and writes a
verification log file ``data/setup_log.json`` that records the successful
creation of the directories.

The script is safe to run multiple times – existing directories are left
untouched and the log file is overwritten with a fresh timestamp.
"""

import json
import datetime
from pathlib import Path

def _determine_repo_root() -> Path:
    """
    Determine the repository root directory.

    The script lives in:
    ``projects/PROJ-175-statistical-analysis-of-publicly-availab/code/``
    so we need to go up four levels:

    - code/
    - PROJ-175-statistical-analysis-of-publicly-availab/
    - projects/
    - <repo_root>
    """
    return Path(__file__).resolve().parents[4]

def _ensure_directories(repo_root: Path) -> list[Path]:
    """
    Create the required directories if they do not already exist.

    Returns a list of the absolute ``Path`` objects that were (or are) present.
    """
    dirs = [
        repo_root / "projects" / "PROJ-175-statistical-analysis-of-publicly-availab" / "code",
        repo_root / "projects" / "PROJ-175-statistical-analysis-of-publicly-availab" / "data",
        repo_root / "projects" / "PROJ-175-statistical-analysis-of-publicly-availab" / "tests",
        repo_root / "data",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return dirs

def _write_setup_log(repo_root: Path, dirs: list[Path]) -> None:
    """
    Write ``data/setup_log.json`` with a success status, the list of verified
    paths (relative to the repository root) and an ISO‑8601 UTC timestamp.
    """
    log_path = repo_root / "data" / "setup_log.json"
    log_content = {
        "status": "SUCCESS",
        "paths_verified": [str(p.relative_to(repo_root)) for p in dirs],
        "timestamp": datetime.datetime.utcnow()
        .replace(microsecond=0)
        .isoformat()
        + "Z",
    }

    with log_path.open("w", encoding="utf-8") as f:
        json.dump(log_content, f, indent=2)

    print(f"Setup log written to {log_path}")

def main() -> None:
    repo_root = _determine_repo_root()
    dirs = _ensure_directories(repo_root)
    _write_setup_log(repo_root, dirs)

if __name__ == "__main__":
    main()
