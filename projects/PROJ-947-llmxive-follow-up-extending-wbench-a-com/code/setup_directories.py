"""
Script to ensure the required directory structure for the llmXive project exists.
This satisfies task T001a and T001c by creating code/, tests/, data/, results/
and the specific test subdirectories.
"""
import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def ensure_checksums_file() -> None:
    """Ensure the checksums.json placeholder exists in data/."""
    data_dir = Path("data")
    checksums_file = data_dir / "checksums.json"
    if not checksums_file.exists():
        checksums_file.write_text("{}")
        print(f"Created placeholder file: {checksums_file}")
    else:
        print(f"Checksums file already exists: {checksums_file}")

def verify_structure() -> bool:
    """Verify that all required directories exist."""
    required_dirs = [
        Path("code"),
        Path("tests"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("tests/contract"),
        Path("data"),
        Path("results"),
    ]
    all_exist = True
    for d in required_dirs:
        if not d.exists():
            print(f"MISSING: {d}")
            all_exist = False
        else:
            print(f"OK: {d}")
    return all_exist

def main() -> int:
    """Main entry point to create the directory structure."""
    print("Initializing llmXive project directory structure...")
    
    # Create root directories
    ensure_directory(Path("code"))
    ensure_directory(Path("tests"))
    ensure_directory(Path("data"))
    ensure_directory(Path("results"))
    
    # Create test subdirectories
    ensure_directory(Path("tests/unit"))
    ensure_directory(Path("tests/integration"))
    ensure_directory(Path("tests/contract"))
    
    # Create placeholder files to ensure directories are tracked by git
    for root_dir in ["code", "tests", "tests/unit", "tests/integration", "tests/contract", "data", "results"]:
        gitkeep = Path(root_dir) / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Placeholder to retain directory in version control\n")
            print(f"Created .gitkeep: {gitkeep}")

    # Ensure checksums file exists
    ensure_checksums_file()

    # Verify
    if verify_structure():
        print("SUCCESS: All required directories and files exist.")
        return 0
    else:
        print("FAILURE: Some required directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())