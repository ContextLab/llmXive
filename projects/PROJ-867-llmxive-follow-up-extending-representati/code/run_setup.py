import sys
from pathlib import Path

# Add the code directory to the path so we can import setup_project
# This assumes run_setup.py is in the code/ directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import main

if __name__ == "__main__":
    main()