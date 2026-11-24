"""T001d: Create the data/results/ directory at the project root.

Verification: after running this script, data/results/ exists.
"""
from pathlib import Path

def main() -> Path:
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    # Keep a .gitkeep so the empty directory is tracked in version control.
    gitkeep = results_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("")
    print(f"OK: {results_dir} exists")
    return results_dir

if __name__ == "__main__":
    main()