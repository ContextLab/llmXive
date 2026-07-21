import os
from pathlib import Path

def create_directories():
    """
    Creates all necessary directories for the project structure.
    This function ensures that the docs/output directory exists as required by T010.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define all required directories
    directories = [
        "data/raw",
        "data/derived",
        "docs/output",
        "tests",
        "code/utils",
        "specs/001-evaluating-the-impact-of-llm-based-code"
    ]
    
    created = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is a directory, not a file
            if not full_path.is_dir():
                raise ValueError(f"Path exists but is not a directory: {full_path}")
    
    return created

if __name__ == "__main__":
    new_dirs = create_directories()
    print(f"Directories created/verified: {new_dirs}")
    # Explicitly verify T010 requirement
    t010_path = Path(__file__).resolve().parent.parent / "docs" / "output"
    if t010_path.exists() and t010_path.is_dir():
        print(f"SUCCESS: T010 directory exists: {t010_path}")
    else:
        raise RuntimeError(f"FAILED: T010 directory missing: {t010_path}")
