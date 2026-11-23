import os
import sys
from pathlib import Path

def create_directories():
    """Create the full project directory structure."""
    base_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/merged",
        "data/synthetic",
        "code",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "artifacts",
        "results",
        "results/shap_analysis",
        "state",
        "logs",
        "logs/archive",
        "specs",
        "contracts",
        "docs",
    ]

    for d in base_dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep in data directories to ensure they are tracked
        if d.startswith("data") or d in ["artifacts", "results", "state", "logs"]:
            gitkeep = path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.write_text(f"# Placeholder for {d}\n")

    # Create specific init files if missing
    (Path("code") / "__init__.py").touch()
    (Path("tests") / "__init__.py").touch()

def main():
    create_directories()
    print("Directory structure created successfully.")

if __name__ == "__main__":
    main()