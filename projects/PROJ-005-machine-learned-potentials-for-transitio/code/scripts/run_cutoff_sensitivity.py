import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.src.data.cutoff_sensitivity import main

if __name__ == "__main__":
    main()