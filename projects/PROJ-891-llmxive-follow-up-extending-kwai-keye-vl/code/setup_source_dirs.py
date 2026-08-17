import os
from pathlib import Path

def main():
    """
    Create the source directory structure for the project.
    Creates: src/generators, src/inference, src/analysis
    """
    project_root = Path(__file__).resolve().parent.parent
    src_root = project_root / "src"
    
    directories = [
        src_root / "generators",
        src_root / "inference",
        src_root / "analysis",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory.relative_to(project_root)}")
    
    # Create __init__.py files to make them proper Python packages
    for directory in directories:
        init_file = directory / "__init__.py"
        init_file.touch(exist_ok=True)
    
    print("Source directory structure setup complete.")

if __name__ == "__main__":
    main()