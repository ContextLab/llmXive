import os
from pathlib import Path

def create_directories():
    """
    Create the src/ directory structure at the repository root:
    src/data, src/analysis, src/viz, src/utils
    """
    root = Path(".")
    src_dirs = [
        root / "src" / "data",
        root / "src" / "analysis",
        root / "src" / "viz",
        root / "src" / "utils",
    ]

    for directory in src_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Verify creation
    assert (root / "src").exists(), "src/ root directory missing"
    assert (root / "src" / "data").exists(), "src/data missing"
    assert (root / "src" / "analysis").exists(), "src/analysis missing"
    assert (root / "src" / "viz").exists(), "src/viz missing"
    assert (root / "src" / "utils").exists(), "src/utils missing"

def main():
    create_directories()

if __name__ == "__main__":
    main()
