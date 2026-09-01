"""
Runner script to execute the project setup.
"""
import sys
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_project import main

if __name__ == "__main__":
    sys.exit(main())