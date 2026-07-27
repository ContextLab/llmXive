"""
Tool to create the src/data-models directory.
This script ensures the directory exists and contains an __init__.py file
to make it a proper Python package, importing from the existing src/data-models.py.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the target directory relative to the project root
    # Assuming this script is run from the project root or tools directory
    project_root = Path(__file__).parent.parent
    target_dir = project_root / "src" / "data-models"

    # Create the directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {target_dir}")

    # Create __init__.py to re-export from the existing data-models.py file
    # The existing file is src/data-models.py (singular), we want to expose it as a package
    init_file = target_dir / "__init__.py"
    
    # We need to import from the sibling file src/data-models.py
    # Since src/data-models.py is a file, not a package, we import its contents
    init_content = '''"""
Data models package for llmXive.
Re-exports EditInstance and ScoreRecord from the main data-models.py file.
"""
from ..data_models import EditInstance, ScoreRecord

__all__ = ["EditInstance", "ScoreRecord"]
'''
    
    try:
        init_file.write_text(init_content)
        print(f"Created package init file: {init_file}")
    except Exception as e:
        print(f"Error creating __init__.py: {e}")
        sys.exit(1)

    # Verify the directory structure
    print(f"Directory structure verified:")
    print(f"  - {target_dir}/")
    print(f"    - __init__.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
