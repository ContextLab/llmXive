import os
from pathlib import Path

def ensure_processed_directory():
    """
    Creates the 'data/processed' directory if it does not exist.
    This fulfills task T004: Create `projects/PROJ-267-exploring-the-relationship-between-atmos/data/processed/` directory.
    """
    # The project root is assumed to be the parent of the 'code' directory
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"

    if not processed_dir.exists():
        processed_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {processed_dir}")
    else:
        print(f"Directory already exists: {processed_dir}")
    
    # Verify creation
    if not processed_dir.is_dir():
        raise RuntimeError(f"Failed to create directory: {processed_dir}")
    
    return processed_dir

def main():
    ensure_processed_directory()

if __name__ == "__main__":
    main()