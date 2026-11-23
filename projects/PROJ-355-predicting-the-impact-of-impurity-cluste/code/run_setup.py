import sys
from pathlib import Path

# Add code directory to path if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from setup_project import main as setup_main

def main():
    """Entry point for running the project setup."""
    return setup_main()

if __name__ == "__main__":
    sys.exit(main())