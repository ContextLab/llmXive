"""
CLI shim for downloading datasets.
"""
import argparse
from code.datasets.openneuro_client import list_datasets
from code.src.datasets.download_datasets import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    
    candidates = list_datasets()
    main(candidates, verify_only=args.verify_only)
    print("Dataset download/verification process completed.")
