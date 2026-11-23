"""
03_feature_extraction.py: Wrapper script for the feature extraction pipeline.

This script reconciles the run-book command `python code/03_feature_extraction.py`
with the actual implementation logic. It orchestrates the canonical feature
extraction workflow defined in `code/02_feature_extraction.py`.

It executes the full feature extraction workflow:
1. Loads cleaned molecules from `data/processed/molecules_cleaned.parquet`.
2. Generates 2D Morgan fingerprints (radius=2, nBits=2048).
3. Generates 3D graph features (atomic number, hybridization, distances, angles, dihedrals).
4. Saves feature matrices (.npy) and labels (.csv) to `data/processed/`.

Dependency: Requires T010 (02_clean.py) to have produced the cleaned parquet file.
"""

import sys
import os
import logging

# Ensure the code directory is in the path for relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.utils.logger import configure_logging_for_pipeline, get_logger
from code_02_feature_extraction import main as feature_extraction_main

logger = get_logger("03_feature_extraction")

def main():
    """
    Entry point for the 03_feature_extraction command.
    Delegates execution to the feature extraction module.
    """
    configure_logging_for_pipeline()
    logger.info("Starting Feature Extraction Pipeline (via code/03_feature_extraction.py)...")
    try:
        feature_extraction_main()
        logger.info("Feature Extraction completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Feature Extraction failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
