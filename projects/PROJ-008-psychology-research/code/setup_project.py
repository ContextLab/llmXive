import os
import sys
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main() -> int:
    """Create the full project directory structure."""
    base = Path(__file__).parent.parent
    structure = [
        base / "code",
        base / "code" / "analysis",
        base / "code" / "data",
        base / "code" / "setup",
        base / "code" / "utils",
        base / "code" / "viz",
        base / "data",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "data" / "interim",
        base / "docs",
        base / "tests",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "tests" / "contract",
        base / "contracts",
        base / "scripts",
        base / ".github" / "workflows",
    ]
    for d in structure:
        ensure_dir(d)
    return 0

if __name__ == "__main__":
    sys.exit(main())