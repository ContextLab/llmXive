import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.stats.sensitivity import main

if __name__ == "__main__":
    main()
