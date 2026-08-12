"""
Script to initialize the project directory structure for llmXive follow-up.
Creates the required folders: src/, tests/, specs/, data/, data/results/, data/manual/.
"""
import os
from pathlib import Path

def create_directory_structure():
    """Create the standard project directory structure."""
    base_dir = Path(__file__).parent.parent  # Assumes script is in code/
    
    # Define required directories relative to project root
    required_dirs = [
        "src",
        "src/analysis",
        "src/data",
        "src/data/cache",
        "src/models",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "specs",
        "data",
        "data/raw",
        "data/interim",
        "data/results",
        "data/manual",
        "figures",
        "code"
    ]

    created = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path.relative_to(base_dir)))
        # Create __init__.py files for Python packages
        if dir_path.startswith("src/") or dir_path.startswith("tests/"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Auto-generated init file\n")
                created.append(str(init_file.relative_to(base_dir)))

    return created

def main():
    """Entry point to run the setup."""
    print("Initializing project directory structure...")
    created = create_directory_structure()
    print(f"Successfully created {len(created)} directories/files:")
    for path in created:
        print(f"  - {path}")
    print("Project structure ready.")

if __name__ == "__main__":
    main()