import os
from pathlib import Path

def create_project_structure(base_dir: str = "projects/001-statistical-evaluation-of-dimensionality") -> None:
    """
    Creates the required project directory structure for the statistical evaluation pipeline.
    
    Creates:
    - data/raw: For downloaded raw count matrices
    - data/processed: For preprocessed data and intermediate files
    - results: For final analysis outputs, reports, and metrics
    - code: For implementation scripts and modules (already exists as root code/ but mirrored here per task spec)
    - tests: For unit and integration tests
    
    Args:
        base_dir: The root directory path for the project structure. Defaults to the project-specific path.
    """
    base_path = Path(base_dir)
    
    # Define the required subdirectories
    directories = [
        "data/raw",
        "data/processed",
        "results",
        "code",
        "tests"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure creation complete.")
    print(f"Total directories created: {created_count}")
    print(f"Base directory: {base_path.resolve()}")
    
    # List the final structure
    print("\nFinal Directory Structure:")
    for dir_path in directories:
        full_path = base_path / dir_path
        print(f"  {full_path.relative_to(base_path)}/")

def main() -> None:
    """Entry point for script execution."""
    create_project_structure()

if __name__ == "__main__":
    main()
