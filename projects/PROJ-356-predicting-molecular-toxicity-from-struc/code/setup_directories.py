import os
import sys
from pathlib import Path

def main():
    """
    Legacy entry point for directory creation.
    Delegates to scripts.create_directories for consistency.
    """
    # Ensure the code directory is in the path if running from root
    code_dir = Path(__file__).resolve().parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    from scripts.create_directories import main as create_main
    return create_main()

if __name__ == "__main__":
    sys.exit(main())
