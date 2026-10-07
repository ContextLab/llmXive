import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from robustness import main as sensitivity_main

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting Mixed Effects Sensitivity Analysis script.")
    sensitivity_main()

if __name__ == "__main__":
    main()