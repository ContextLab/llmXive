import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def create_placeholder_file(path: Path, content: str = "# Placeholder\n") -> None:
    """Create a placeholder file if it does not exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

def main() -> None:
    """
    Create the full project structure for PROJ-532.
    This script is idempotent and safe to run multiple times.
    """
    base = Path("projects/PROJ-532-predicting-material-degradation-pathways")

    # Core directories
    dirs = [
        base / "code",
        base / "data",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "data" / "contracts",
        base / "results",
        base / "results" / "metrics",
        base / "results" / "plots",
        base / "results" / "artifacts",
        base / "tests",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "specs",
        base / "docs",
    ]

    for d in dirs:
        ensure_dir(d)

    # Create essential files
    (base / "README.md").touch()
    (base / "requirements.txt").touch()
    (base / "code" / "__init__.py").touch()
    (base / "tests" / "__init__.py").touch()

    # Create .gitkeep in empty directories to ensure they are tracked
    for d in dirs:
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep directory\n", encoding='utf-8')

    print(f"Project structure created at: {base}")

if __name__ == "__main__":
    main()
