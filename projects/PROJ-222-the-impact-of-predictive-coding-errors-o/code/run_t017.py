import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generate_standardized_output import main

if __name__ == "__main__":
    main()
