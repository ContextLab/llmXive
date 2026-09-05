import sys
from pathlib import Path

# Ensure the code directory is in the path
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.stats.robustness_interpreter import main

if __name__ == "__main__":
    sys.exit(main())
