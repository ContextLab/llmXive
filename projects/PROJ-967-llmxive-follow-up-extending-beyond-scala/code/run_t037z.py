import sys
from pathlib import Path

# Add the code directory to the path to allow imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data_availability_logger import main

if __name__ == "__main__":
    sys.exit(main())
