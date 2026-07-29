import sys
from pathlib import Path

# Add project root to path if running from code/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.templates.fetcher import main

if __name__ == "__main__":
    main()
