#!/usr/bin/env python3
"""
Standalone runner for the archive pipeline task (T005d).

This script copies downloaded raw data files to the archive directory
and computes SHA-256 checksums for integrity verification.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.archive_pipeline import main

if __name__ == "__main__":
    sys.exit(main())