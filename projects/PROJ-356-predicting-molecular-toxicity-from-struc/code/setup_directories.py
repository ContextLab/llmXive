import os
import sys
from pathlib import Path

def main():
    """Create all required project directories."""
    # Determine project root (parent of code/)
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent

    # Directories to create
    dirs = [
        code_dir / "src",
        code_dir / "tests",
        code_dir / "data",
        code_dir / "results",
        code_dir / "models",
        code_dir / "config",
        project_root / "docs",
    ]

    created = []
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        created.append(str(d))

    print("Created directories:")
    for d in created:
        print(f"  {d}")

    return created

if __name__ == "__main__":
    main()