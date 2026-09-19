import os
from pathlib import Path

def main():
    """
    Creates the 'results/' directory if it does not exist.
    This task corresponds to T001c in the project plan.
    """
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / "results"
    
    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {results_dir}")
    else:
        print(f"Directory already exists: {results_dir}")

if __name__ == "__main__":
    main()
