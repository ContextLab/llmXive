import os
from pathlib import Path

def main():
    """
    Legacy wrapper to ensure outputs directory exists.
    Now subsumed by setup_directories.py, but kept for API compatibility.
    """
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    outputs_dir = project_root / "outputs"
    if not outputs_dir.exists():
        outputs_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created outputs directory: {outputs_dir}")
    else:
        print(f"Outputs directory already exists: {outputs_dir}")
    return 0

if __name__ == "__main__":
    exit(main())