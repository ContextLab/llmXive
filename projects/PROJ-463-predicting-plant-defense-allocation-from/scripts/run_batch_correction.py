"""
CLI script to run batch correction on real or synthetic data.
"""
import sys
import argparse
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.data.batch_correction import main

if __name__ == "__main__":
    main()