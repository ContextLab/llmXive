import os
from pathlib import Path
from typing import List

def create_specs_directories(base_path: Path) -> List[str]:
    """
    Creates the required directory structure for the project specifications.
    
    Specifically creates:
    projects/PROJ-405/specs/001-predict-plant-disease-severity/
    .../contracts/
    .../designs/
    .../notes/
    
    Args:
        base_path: The root path of the project (e.g., projects/PROJ-405)
        
    Returns:
        List of created directory paths as strings.
    """
    project_root = base_path
    specs_root = project_root / "specs"
    feature_root = specs_root / "001-predict-plant-disease-severity"
    
    directories = [
        feature_root,
        feature_root / "contracts",
        feature_root / "designs",
        feature_root / "notes",
    ]
    
    created_paths = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(dir_path))
        
    return created_paths

def main():
    """
    Entry point for creating the specs directory structure.
    Assumes execution from the project root (projects/PROJ-405).
    """
    base_path = Path.cwd()
    # Verify we are in the expected project root or handle relative path
    if not (base_path / "code").exists():
        # If running from a parent, try to locate the project root
        # For T001c, we assume the script is run from projects/PROJ-405
        pass
        
    created = create_specs_directories(base_path)
    print(f"Created specification directories in {base_path}:")
    for p in created:
        print(f"  - {p}")

if __name__ == "__main__":
    main()
