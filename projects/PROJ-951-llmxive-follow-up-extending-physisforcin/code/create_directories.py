import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    Implements Task T001b: Create src/, tests/, data/ and specific module directories.
    """
    # Project root relative to the code directory
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the base directories relative to project root
    # Note: The task specifies creating these under the project root.
    # Based on T001 context, the project root is PROJ-951-...
    # The code/ directory is inside that.
    # We will create the structure relative to the directory where this script is run,
    # or explicitly relative to the project root if we assume standard layout.
    # Given the task description: "Create src/, tests/, data/ subdirectories"
    # and the path conventions "Single project: src/, tests/ at repository root",
    # we assume the script is run from the project root or creates it relative to itself.
    # To be safe and consistent with T001 (which created code/), we create these 
    # relative to the parent of code/ (the project root).
    
    base_path = project_root
    
    directories = [
        # Core project directories
        "src",
        "tests",
        "data",
        
        # Data subdirectories
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation",
        
        # Source module directories
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/utils",
        
        # Test subdirectories
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory creation complete. {created_count} new directories created.")
    print(f"Base path used: {base_path}")
    
    # Verify structure
    print("\nVerifying structure...")
    missing = []
    for dir_path in directories:
        if not (base_path / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"WARNING: The following directories are missing: {missing}")
        return 1
    else:
        print("All required directories verified.")
        return 0

if __name__ == "__main__":
    exit(main())
