import sys
from pathlib import Path

# Add the code directory to the path so we can import from src
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from src.stats.robustness_interpreter import main

if __name__ == '__main__':
    main()
