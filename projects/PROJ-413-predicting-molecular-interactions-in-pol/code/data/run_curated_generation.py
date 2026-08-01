#!/usr/bin/env python3
"""
Script to execute the curated dataset generation pipeline.
This serves as the entry point for the execution stage.
"""
import sys
from pathlib import Path

# Add code root to path
code_root = Path(__file__).resolve().parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data.generate_curated import main

if __name__ == "__main__":
    main()