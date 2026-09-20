import sys
from pathlib import Path
from setup_project import main as setup_main

def main() -> int:
    """
    Entry point for running the project setup script.
    Delegates to setup_project.main().
    """
    return setup_main()

if __name__ == "__main__":
    sys.exit(main())