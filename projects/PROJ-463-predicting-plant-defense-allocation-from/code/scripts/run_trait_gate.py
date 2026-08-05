import sys
from pathlib import Path

# Add the project root to the path if necessary
# Assuming the script is run from the project root or code/
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.traits_gate import main

if __name__ == "__main__":
    main()
