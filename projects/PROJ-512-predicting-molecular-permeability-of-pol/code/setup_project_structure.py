"""Create the standard project directory structure defined in plan.md.

Structure (per plan.md "Project Structure" and tasks.md T001a):
- code/data/raw/         : raw downloaded data (polymer_raw.csv, checksums.json)
- code/data/processed/   : processed data (polymers.h5, scaffold_split_indices.json)
- code/models/           : model code and trained model artifacts
- code/evaluation/results: evaluation results (metrics.json, sensitivity_sweep.json)
- code/logs/             : pipeline logs

The script is idempotent: running it twice is safe. It creates the
directories and drops a .gitkeep file in each so the empty directories
are preserved by version control.
"""
import sys
from pathlib import Path

def create_structure() -> list:
    """Create all directories required by plan.md; return list of created dirs."""
    code_root = Path(__file__).resolve().parent
    required_dirs = [
        code_root / "data" / "raw",
        code_root / "data" / "processed",
        code_root / "models",
        code_root / "evaluation" / "results",
        code_root / "logs",
    ]
    created = []
    for d in required_dirs:
        existed = d.exists()
        d.mkdir(parents=True, exist_ok=True)
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")
        if not existed:
            created.append(str(d))
    return created

def main() -> int:
    created = create_structure()
    if created:
        print("Created directories:")
        for d in created:
            print(f"  {d}")
    else:
        print("Directory structure already present; nothing to create.")
    # Verify the full expected structure exists before reporting success.
    code_root = Path(__file__).resolve().parent
    expected = [
        code_root / "data" / "raw",
        code_root / "data" / "processed",
        code_root / "models",
        code_root / "evaluation" / "results",
    ]
    missing = [str(d) for d in expected if not d.is_dir()]
    if missing:
        print(f"ERROR: missing directories after setup: {missing}", file=sys.stderr)
        return 1
    print("Project directory structure verified OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
