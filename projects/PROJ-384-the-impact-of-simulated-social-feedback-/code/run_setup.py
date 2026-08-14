import sys
from pathlib import Path

# Ensure the current directory is in the path to import setup_structure
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from setup_structure import create_directories

def main():
    print("Initializing project structure...")
    create_directories()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
