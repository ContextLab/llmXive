"""
Main orchestration script for the llmXive drift detection pipeline.

This script executes the full scoring pipeline:
1. Ensures directories exist.
2. Sets random seeds for reproducibility.
3. (Optional) Builds taxonomy centroids if data/raw/taxonomy.json exists.
4. Runs the drift scoring pipeline on available log data.
5. Exports results to data/processed/drift_scores.csv.

Usage:
    python code/main.py
"""

import sys
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import set_seed, ensure_directories, get_path, get_config
from taxonomy_builder import main as build_taxonomy
from drift_scoring import main as run_drift_scoring
from data_loader import validate_data_integrity
from utils import load_json_file


def main():
    """
    Orchestrates the full drift detection pipeline.
    """
    print("Starting llmXive Drift Detection Pipeline...")
    
    # 1. Setup
    config = get_config()
    set_seed(config.get("random_seed", 42))
    ensure_directories()
    
    raw_data_path = get_path("raw_logs")
    taxonomy_path = get_path("taxonomy")
    centroids_path = get_path("centroids")
    
    # 2. Validate Data Integrity
    print("Validating raw data integrity...")
    if not validate_data_integrity():
        print("ERROR: Data integrity check failed. Aborting.")
        sys.exit(1)
    
    # 3. Build Taxonomy (if source exists and centroids missing)
    if Path(taxonomy_path).exists():
        if not Path(centroids_path).exists():
            print("Taxonomy found, but centroids missing. Building centroids...")
            build_taxonomy()
        else:
            print("Centroids already exist. Skipping taxonomy build.")
    else:
        print("WARNING: No taxonomy source found at {}. Skipping centroid build.".format(taxonomy_path))
        print("Drift scoring may fail or produce default results if centroids are missing.")

    # 4. Run Drift Scoring
    print("Running drift scoring pipeline...")
    try:
        run_drift_scoring()
        print("Drift scoring completed successfully.")
    except Exception as e:
        print(f"ERROR: Drift scoring pipeline failed: {e}")
        sys.exit(1)

    print("Pipeline execution finished.")


if __name__ == "__main__":
    main()