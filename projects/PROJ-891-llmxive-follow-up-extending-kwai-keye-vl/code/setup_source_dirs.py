import os
from pathlib import Path

def main():
    """
    Create the source directory structure required for the project.
    Creates: src/generators, src/inference, src/analysis
    """
    project_root = Path(__file__).resolve().parent
    src_root = project_root / "src"
    
    directories = [
        "generators",
        "inference",
        "analysis"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = src_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py to make it a Python package
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created_count += 1
        else:
            created_count += 1 # Count as created if it exists too
        
        print(f"Ensured existence of: {dir_path}")
    
    print(f"Source directory structure setup complete. Created/verified {created_count} directories.")

if __name__ == "__main__":
    main()
