"""
T001: Create the project directory structure per the implementation plan.

Creates every directory listed in tasks.md T001 and writes an evidence
manifest (JSON) recording each created path, so the directory layout can
be verified without a screenshot.

Output: data/intermediate/project_structure_manifest.json

Uses only the standard library so it runs before any project config
dependencies are installed or fixed.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code/01_data_collection",
    "code/02_static_analysis",
    "code/03_statistical_analysis",
    "code/04_reporting",
    "code/utils",
    "tests/contract",
    "tests/integration",
    "tests/unit",
    "data/raw/human_samples",
    "data/raw/llm_samples",
    "data/intermediate",
    "data/processed",
    "reports",
    "specs/001-code-smell-comparison",
]

MANIFEST_PATH = PROJECT_ROOT / "data" / "intermediate" / "project_structure_manifest.json"


def create_structure(root: Path = PROJECT_ROOT) -> dict:
    """Create all required directories under root and return a manifest dict."""
    entries = []
    all_ok = True
    for rel in REQUIRED_DIRS:
        target = root / rel
        existed = target.is_dir()
        try:
            target.mkdir(parents=True, exist_ok=True)
            ok = target.is_dir()
        except OSError as exc:
            ok = False
            print(f"ERROR: could not create {target}: {exc}", file=sys.stderr)
        all_ok = all_ok and ok
        entries.append({
            "path": rel,
            "exists": ok,
            "existed_before": existed,
        })

    manifest = {
        "task_id": "T001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root),
        "all_directories_present": all_ok,
        "directories": entries,
    }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main() -> int:
    manifest = create_structure()
    print(f"Created {len(manifest['directories'])} directories under {manifest['project_root']}")
    print(f"Evidence manifest written to {MANIFEST_PATH}")
    if not manifest["all_directories_present"]:
        print("ERROR: some directories could not be created", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())