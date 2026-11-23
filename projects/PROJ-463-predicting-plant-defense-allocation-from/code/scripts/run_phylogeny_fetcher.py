"""
Script runner for phylogeny fetcher (T028a).
"""

import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.phylogeny_fetcher import main

if __name__ == "__main__":
    sys.exit(main())
