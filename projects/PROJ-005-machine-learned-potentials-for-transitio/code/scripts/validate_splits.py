import sys
import logging
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(code_dir))

from src.data.validate_splits import main

if __name__ == '__main__':
    main()