"""
Script to initialize the project directory structure.
Creates required directories: code/, tests/, data/raw, data/processed, data/models.
"""
import os
from pathlib import Path

def main():
    """Create all necessary project directories."""
    root = Path.cwd()
    
    # Core directories
    dirs_to_create = [
        root / "code",
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "models",
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_content = "# Placeholder to ensure directory is tracked by version control.\n"
    gitkeep_dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "models",
    ]
    
    for dir_path in gitkeep_dirs:
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            with open(gitkeep_path, 'w') as f:
                f.write(gitkeep_content)
            print(f"Created .gitkeep in: {dir_path}")
            created_count += 1

    # Create __init__.py files if missing
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "tests" / "unit" / "__init__.py",
        root / "tests" / "integration" / "__init__.py",
    ]
    
    for init_path in init_files:
        if not init_path.exists():
            with open(init_path, 'w') as f:
                f.write('"""Package initialization."""\n')
            print(f"Created init file: {init_path}")
            created_count += 1

    print(f"\nSetup complete. {created_count} new items created.")

if __name__ == "__main__":
    main()