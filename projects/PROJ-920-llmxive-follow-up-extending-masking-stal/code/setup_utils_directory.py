"""
Utility script to create the code/utils/ directory for the llmXive project.
This script ensures the directory exists and is ready for utility modules.
"""
import os
from pathlib import Path

def main():
    """Create the code/utils/ directory if it does not exist."""
    project_root = Path("projects/PROJ-920-llmxive-follow-up-extending-masking-stal")
    utils_dir = project_root / "code" / "utils"
    
    utils_dir.mkdir(parents=True, exist_ok=True)
    print(f"Directory created: {utils_dir}")
    
    # Create __init__.py to make it a proper Python package
    init_file = utils_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("")
        print(f"Created package initializer: {init_file}")
    else:
        print(f"Package initializer already exists: {init_file}")

if __name__ == "__main__":
    main()
