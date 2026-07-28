"""
Entry point to execute the project structure setup.
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_structure import create_directories

if __name__ == "__main__":
    print("Initializing project structure...")
    success = create_directories()
    if success:
        print("Project structure initialization complete.")
        sys.exit(0)
    else:
        print("Failed to initialize project structure.")
        sys.exit(1)