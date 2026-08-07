"""
extract_features.py: Entry point for feature extraction.

This script serves as the canonical entry point for the feature extraction logic
as referenced by the run-book and internal tests. It delegates to the implementation
in `code/02_feature_extraction.py`.
"""

import sys
import os

# Ensure the code directory is in the path for relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main logic from the implementation module
from code_02_feature_extraction import main as feature_extraction_main

def main():
    """
    Entry point for the extract_features command.
    Delegates execution to the feature extraction module.
    """
    print("Starting Feature Extraction Pipeline (via code/extract_features.py)...")
    try:
        feature_extraction_main()
        print("Feature Extraction completed successfully.")
    except Exception as e:
        print(f"Feature Extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
