"""Create the data/raw directory for PROJ-066 (Task T008a).

Ensures projects/PROJ-066-investigating-correlations-between-molec/data/raw/
exists on disk and contains a .gitkeep placeholder so the (otherwise empty)
directory is preserved in version control.
"""
from pathlib import Path

from llmxive_toolkit import paths

def main() -> None:
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = raw_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text(
            "Placeholder to keep data/raw/ in version control.\n"
            "Raw ChEMBL 33 artifacts (chembl_33.db, chembl_33.sha256) are\n"
            "downloaded here by code/data/download.py (Task T009).\n"
        )
    print(f"Created directory: {raw_dir}")
    print(f"Contents: {sorted(p.name for p in raw_dir.iterdir())}")

if __name__ == "__main__":
    main()