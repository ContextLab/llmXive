#!/usr/bin/env python3
"""T001a: Create the project directory structure per the implementation plan.

Creates (idempotently) the directories:
  code/, tests/, data/, data/raw/, data/processed/, data/results/,
  data/logs/, scripts/

and writes a .gitkeep file in each empty directory so the structure is
preserved in version control. A manifest of the created structure is
written to data/logs/directory_structure.json as evidence.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/logs",
    "scripts",
]

def main() -> None:
    created = []
    existing = []
    for rel in DIRECTORIES:
        d = PROJECT_ROOT / rel
        if d.is_dir():
            existing.append(rel)
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
        # keep empty dirs in git
        gitkeep = d / ".gitkeep"
        if not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            gitkeep.touch()

    manifest = {
        "task_id": "T001a",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "directories": DIRECTORIES,
        "created": created,
        "already_existed": existing,
    }
    logs_dir = PROJECT_ROOT / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = logs_dir / "directory_structure.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    # Verify
    missing = [rel for rel in DIRECTORIES if not (PROJECT_ROOT / rel).is_dir()]
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")

    print("Directory structure verified:")
    for rel in DIRECTORIES:
        print(f"  {rel}/")
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()