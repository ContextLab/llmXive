"""
Script to run the Router Convergence Validation (Task T053).
"""

import os
import sys
import logging
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from router_convergence_validator import main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    main()