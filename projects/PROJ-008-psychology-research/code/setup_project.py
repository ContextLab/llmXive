"""
Setup script to ensure project directories exist.
"""
import os
import sys
from pathlib import Path

def ensure_dir(path_str: str) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path_str)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Create standard project directories."""
    base = Path(__file__).parent.parent
    dirs = [
        base / "code",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "data" / "interim",
        base / "docs",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "tests" / "contract",
        base / "contracts",
        base / "scripts",
        base / ".github" / "workflows",
    ]
    for d in dirs:
        ensure_dir(str(d))
        print(f"Ensured directory: {d}")

if __name__ == "__main__":
    main()
