"""
Runner script for T016: Save generated CSVs.

This script orchestrates the generation and saving of all required datasets.
It ensures T015-ENFORCE passes before proceeding.
"""
import sys
from generators.save_datasets import main

if __name__ == "__main__":
    sys.exit(main())
