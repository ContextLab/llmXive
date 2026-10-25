"""
Alias for code/datasets/download_datasets.py to satisfy quickstart.md.
"""
import sys
import os
from pathlib import Path

# This script simply invokes the main download logic
from code.datasets.download_datasets import list_datasets
from code.src.datasets.download_datasets import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    
    candidates = list_datasets()
    main(candidates, verify_only=args.verify_only)
    print("OpenNeuro data acquisition completed.")
