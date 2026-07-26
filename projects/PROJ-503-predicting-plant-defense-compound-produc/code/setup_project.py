import os
import sys
from pathlib import Path

def setup_project_structure():
    """
    Creates the required directory structure for the plant defense compound prediction project.
    Implements T001: Create project structure with exact directories.
    """
    base_path = Path("projects/PROJ-503-predicting-plant-defense-compound-produc")
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/paired",
        "logs",
        "outputs/models",
        "docs",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    
    created_dirs = []
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create placeholder files to ensure directories are non-empty (for verification)
    # This helps satisfy the "non-empty" verification requirement mentioned in T001 rejection
    placeholders = [
        ("logs/.gitkeep", "Log directory placeholder"),
        ("docs/.gitkeep", "Documentation directory placeholder"),
        ("data/raw/.gitkeep", "Raw data directory placeholder"),
        ("data/processed/.gitkeep", "Processed data directory placeholder"),
        ("data/paired/.gitkeep", "Paired data directory placeholder"),
        ("outputs/models/.gitkeep", "Model outputs directory placeholder"),
        ("tests/contract/.gitkeep", "Contract tests placeholder"),
        ("tests/integration/.gitkeep", "Integration tests placeholder"),
        ("tests/unit/.gitkeep", "Unit tests placeholder"),
    ]
    
    for file_path, content in placeholders:
        full_file_path = base_path / file_path
        if not full_file_path.exists():
            full_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_file_path, 'w') as f:
                f.write(f"# {content}\n")
    
    return {
        "status": "success",
        "base_path": str(base_path),
        "created_directories": created_dirs,
        "total_directories": len(directories),
        "message": f"Project structure created successfully at {base_path}"
    }

def main():
    """Main entry point for project setup."""
    print("Setting up project structure for PROJ-503...")
    try:
        result = setup_project_structure()
        print(f"✓ {result['message']}")
        print(f"  Created {len(result['created_directories'])} new directories")
        print(f"  Total directories: {result['total_directories']}")
        
        # Verify structure exists
        base_path = Path("projects/PROJ-503-predicting-plant-defense-compound-produc")
        required_dirs = [
            "code", "data/raw", "data/processed", "data/paired",
            "logs", "outputs/models", "docs",
            "tests/contract", "tests/integration", "tests/unit"
        ]
        
        all_exist = True
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                print(f"✗ Missing or invalid: {dir_path}")
                all_exist = False
            else:
                print(f"✓ {dir_path}/")
        
        if all_exist:
            print("\n✓ All required directories verified successfully")
            return 0
        else:
            print("\n✗ Some directories are missing or invalid")
            return 1
            
    except Exception as e:
        print(f"✗ Error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())