import os
from pathlib import Path

def main():
    """Create the project directory structure as defined in tasks.md T001."""
    # Define the root directory relative to the script location or current working directory
    # The project structure assumes code/ is the root for artifacts, but tasks.md says 'src/' at root.
    # Based on the 'Existing project API surface' provided, files are under 'code/'.
    # We will create the structure under 'code/' to match the existing API surface paths.
    # The task description says: `mkdir -p src/ingestion ...`
    # The existing files are at `code/src/ingestion/...`.
    # We will create the directories under `code/` to ensure the existing imports work.
    
    base_path = Path(__file__).parent.parent  # points to code/
    
    directories = [
        "src/ingestion",
        "src/modeling",
        "src/visualization",
        "src/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "docs"
    ]
    
    created = []
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Even if exists, we verify it's a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Output evidence of structure creation
    print("Project structure verification:")
    for dir_name in directories:
        full_path = base_path / dir_name
        status = "EXISTS" if full_path.is_dir() else "MISSING"
        print(f"  [{status}] {full_path}")
        
    if created:
        print(f"\nCreated {len(created)} new directories.")
    else:
        print("\nAll directories already existed.")

if __name__ == "__main__":
    main()
