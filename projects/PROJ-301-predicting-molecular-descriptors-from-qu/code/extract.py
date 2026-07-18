"""
Extract: Wrapper script for the feature extraction pipeline.

This script reconciles the run-book command `python code/extract.py` with the
actual implementation located in `code/02_feature_extraction.py`.

It executes the full feature extraction workflow:
1. Loads cleaned molecules from `data/processed/molecules_cleaned.parquet`.
2. Generates 2D Morgan fingerprints.
3. Generates 3D graph features (atomic, hybridization, distance, angles).
4. Splits data into train/test sets.
5. Saves feature matrices (.npy) and labels (.csv) to `data/processed/`.

Dependency: Requires T010 (02_clean.py) to have produced the cleaned parquet file.
"""

import sys
import os

# Ensure the code directory is in the path for relative imports if running as script
# However, since this is a wrapper, we import the main logic directly.
# The actual implementation is in 02_feature_extraction.py

# We need to add the code directory to sys.path to import 02_feature_extraction
# if the script is run from the project root.
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code_02_feature_extraction import main as feature_extraction_main

def main():
    """
    Entry point for the extract command.
    Delegates execution to the feature extraction module.
    """
    print("Starting Feature Extraction Pipeline (via code/extract.py)...")
    try:
        feature_extraction_main()
        print("Feature Extraction completed successfully.")
    except Exception as e:
        print(f"Feature Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
