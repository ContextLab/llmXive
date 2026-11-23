import os
from pathlib import Path

def verify_structure():
    """Verify that all required directories exist."""
    base = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    required_dirs = [
        base,
        base / "src",
        base / "src" / "data",
        base / "src" / "train",
        base / "src" / "eval",
        base / "src" / "analyze",
        base / "src" / "utils",
        base / "tests",
        base / "tests" / "contract",
        base / "tests" / "integration",
    ]
    
    all_exist = True
    for d in required_dirs:
        if not d.exists():
            print(f"MISSING: {d}")
            all_exist = False
        else:
            print(f"OK: {d}")
    
    if all_exist:
        print("\nAll required directories exist.")
        return 0
    else:
        print("\nSome directories are missing.")
        return 1

def main():
    exit_code = verify_structure()
    exit(exit_code)

if __name__ == "__main__":
    main()