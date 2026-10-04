import sys
from pathlib import Path

# Add the code directory to the path so we can import src modules
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.data.generate_final_artifacts import main

if __name__ == "__main__":
    main()
