"""
Utility script to compute SHA‑256 checksums for all raw data files.

This script is part of task **T001a**. It invokes the ``compute_checksums``
function from the utils module which also records the manifest in the
project‑level ``project_state.yaml`` file.
"""
import sys
from pathlib import Path

# Import the compute_checksums function from the utils module
from utils import compute_checksums

def main():
    try:
        # The function defaults to the conventional raw data directory
        compute_checksums()
    except Exception as e:
        print(f"Error during checksum computation: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()