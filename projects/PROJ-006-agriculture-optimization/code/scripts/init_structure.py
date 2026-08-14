"""
Initialization script for the project structure.
This is a wrapper that ensures the core structure is in place.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Initialize the core project structure."""
    project_root = Path(__file__).resolve().parent.parent

    # Core directories
    core_dirs = ["src", "tests", "contracts", "data", "reports", "figures", "docs"]
    for d in core_dirs:
        ensure_dir(project_root / d)

    # Create README placeholder if missing
    readme = project_root / "README.md"
    if not readme.exists():
        readme.write_text(
            "# PROJ-006 Agriculture Optimization\n\n"
            "Automated science pipeline for correlational analysis of "
            "climate-smart agricultural practices.\n"
        )

    print(f"Core structure initialized at: {project_root}")

if __name__ == "__main__":
    main()