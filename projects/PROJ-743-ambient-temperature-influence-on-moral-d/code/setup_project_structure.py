import os
import sys
from pathlib import Path

def ensure_directories():
    """
    Creates the required project directory structure as per the implementation plan.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - results/figures/
    - results/logs/
    - results/stats/
    - tests/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests",
        # Additional standard directories often needed
        "contracts",
        "state/projects",
        "data/external",
        "docs"
    ]

    created_count = 0
    for dir_name in required_dirs:
        target_path = base_path / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure they are directories (idempotent)
        elif not target_path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {target_path}")
    
    return created_count

def main():
    try:
        count = ensure_directories()
        print(f"Project structure setup complete. Created {count} new directories.")
        sys.exit(0)
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()