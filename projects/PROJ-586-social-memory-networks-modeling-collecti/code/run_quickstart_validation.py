"""Entry point for quickstart validation task (T031).

This script executes the quickstart validation process as defined in task T031.
It runs all commands from quickstart.md and verifies exit codes.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.quickstart_validator import main

if __name__ == "__main__":
    sys.exit(main())
