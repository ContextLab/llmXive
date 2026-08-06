import os
from pathlib import Path

def setup_data_directories():
    """Create the required directory structure and __init__.py files."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directories to create relative to the project root
    directories = [
        "src",
        "data/raw",
        "data/processed",
        "data/processed/plots",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path.relative_to(base_dir)))
        
        # Create __init__.py in test directories and src
        if dir_path.startswith("tests") or dir_path == "src":
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                created_dirs.append(f"{dir_path}/__init__.py")
    
    # Create __init__.py for nested test directories if not already done
    # (ensure tests/unit and tests/integration have __init__.py)
    for sub_dir in ["tests/unit", "tests/integration"]:
        full_path = base_dir / sub_dir
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created_dirs.append(f"{sub_dir}/__init__.py")
    
    return created_dirs

def main():
    """Entry point for project setup."""
    print("Setting up project structure...")
    created = setup_data_directories()
    print("Created directories and init files:")
    for item in created:
        print(f"  - {item}")
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()