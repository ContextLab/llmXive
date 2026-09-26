"""
Script runner for metadata verification.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.verify_metadata import main

def main_entry():
    parser = argparse.ArgumentParser(description="Run metadata verification")
    parser.add_argument(
        "--mode",
        choices=["real", "synthetic"],
        default="real",
        help="Mode to run in: real or synthetic",
    )
    args = parser.parse_args()

    main(mode=args.mode)

if __name__ == "__main__":
    main_entry()
