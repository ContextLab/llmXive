"""Create the project's data and output directory structure (Task T001i).

Creates data/raw/, data/processed/, and output/ (with the output
subdirectories named in plan.md) and places .gitkeep files so the
directories persist in version control rather than being empty/missing.

Usage: python code/setup_dirs.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "data/raw",
    "data/processed",
    "output",
    "output/baseline_stories",
    "output/counterfactual_reports",
    "output/integrated_stories",
]

def create_directories(root: Path = PROJECT_ROOT, dirs=None) -> list:
    """Create each directory under root and drop a .gitkeep marker in it.

    Returns the list of created directory paths.
    """
    created = []
    targets = dirs if dirs is not None else DIRECTORIES
    for rel in targets:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
        created.append(d)
    return created

def main() -> int:
    created = create_directories()
    for d in created:
        print(f"OK: {d.relative_to(PROJECT_ROOT)}")
    # Verify all declared directories exist and are non-empty (marker file).
    missing = [d for d in created if not (d / ".gitkeep").is_file()]
    if missing:
        print(f"FAILED: missing marker in {[str(m) for m in missing]}", file=sys.stderr)
        return 1
    print("Directory structure created successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())