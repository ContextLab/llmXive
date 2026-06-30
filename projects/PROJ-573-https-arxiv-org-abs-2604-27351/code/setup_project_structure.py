import os
from pathlib import Path

def create_directories():
    """Create the required project directory structure."""
    base_path = Path(".")
    
    # Define all required directories based on plan.md and tasks.md
    directories = [
        "src",
        "tests",
        "data",
        "data/processed",
        "state",
        "contracts",
        "src/benchmark",
        "src/models",
        "src/tasks",
        "src/evaluation",
        "src/utils",
        "src/benchmark/config",
        "src/benchmark/config/modalities",
        "src/research",
        "src/validators",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/processed",
        "figures",
        "state/projects",
    ]
    
    created = []
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
        else:
            # Ensure it's actually a directory if it exists
            if full_path.is_dir():
                created.append(dir_path)
    
    return created

def create_init_files():
    """Create __init__.py files in all src and tests subdirectories to make them packages."""
    base_path = Path(".")
    
    # Directories that should contain __init__.py
    package_dirs = [
        "src",
        "src/benchmark",
        "src/benchmark/config",
        "src/benchmark/config/modalities",
        "src/models",
        "src/tasks",
        "src/evaluation",
        "src/utils",
        "src/research",
        "src/validators",
        "src/data",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]
    
    created = []
    for dir_path in package_dirs:
        full_path = base_path / dir_path
        init_file = full_path / "__init__.py"
        
        # Create directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if it doesn't exist
        if not init_file.exists():
            init_file.touch()
            created.append(str(init_file))
    
    return created

def main():
    """Main entry point to create project structure."""
    print("Creating project directory structure...")
    
    directories = create_directories()
    if directories:
        print(f"Created {len(directories)} directories:")
        for d in directories:
            print(f"  - {d}")
    else:
        print("All directories already exist.")
    
    print("\nCreating __init__.py files for packages...")
    init_files = create_init_files()
    if init_files:
        print(f"Created {len(init_files)} __init__.py files:")
        for f in init_files:
            print(f"  - {f}")
    else:
        print("All __init__.py files already exist.")
    
    print("\nProject structure setup complete.")

if __name__ == "__main__":
    main()