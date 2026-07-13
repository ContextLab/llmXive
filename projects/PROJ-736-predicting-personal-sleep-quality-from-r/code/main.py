"""
Main orchestration script for the sleep quality prediction pipeline.
Coordinates data download, preprocessing, feature engineering, and modeling.
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error
from data.download_hcp import main as download_main, filter_subjects
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main

def run_pipeline():
    """
    Orchestration function for the sleep quality prediction pipeline.
    Executes the following stages in order:
    1. Download raw HCP data (T005)
    2. Filter subjects based on Sleep Score and Motion (T007b)
    3. Preprocess time series (T006)
    4. Compute connectivity vectors (T007)
    5. Save outputs to data/processed/
    """
    start_time = time.time()
    paths = get_paths()
    ensure_dirs()

    # Setup logging
    logger = setup_logging(paths['log_file'])
    logger.info("Pipeline started")

    try:
        # Stage 1: Download raw data
        log_stage_start(logger, "Data Download")
        # Invoke the download function from download_hcp.py
        # This fetches HCP minimally preprocessed CIFTI files and behavioral data
        download_main()
        log_stage_complete(logger, "Data Download")

        # Stage 2: Filter subjects (T007b logic integrated here or called explicitly)
        # The download_main should have produced the behavioral file.
        # We now filter subjects based on Sleep Score and Motion.
        log_stage_start(logger, "Subject Filtering")
        # Note: filter_subjects is imported from download_hcp. 
        # Depending on implementation, it might need to be called here to update the filtered list.
        # Assuming filter_subjects writes a filtered list or updates the behavioral file.
        # We call it to ensure the filtering logic is applied.
        filtered_subjects = filter_subjects()
        log_stage_complete(logger, "Subject Filtering", extra={"count": len(filtered_subjects)})

        # Stage 3: Preprocess time series (T006)
        log_stage_start(logger, "Preprocessing")
        # Invoke preprocessing on the filtered subjects
        preprocess_main(filtered_subjects)
        log_stage_complete(logger, "Preprocessing")

        # Stage 4: Feature Engineering (T007)
        log_stage_start(logger, "Feature Engineering")
        # Invoke feature engineering on the filtered subjects
        # This step computes pairwise correlations, applies Fisher-z, and extracts vectors
        feature_main(filtered_subjects)
        log_stage_complete(logger, "Feature Engineering")

        # Stage 5: Aggregate and save final outputs
        log_stage_start(logger, "Aggregation and Saving")
        # Load all feature vectors and save as a single .npy file
        from data.feature_engineering import load_feature_vectors
        feature_matrix, final_subjects = load_feature_vectors(filtered_subjects)
        
        # Save the feature matrix
        output_path = paths['processed_dir'] / "connectivity_matrix.npy"
        np.save(output_path, feature_matrix)
        logger.info(f"Saved connectivity matrix to {output_path}")
        
        # Save subject IDs
        subjects_path = paths['processed_dir'] / "subject_ids.npy"
        np.save(subjects_path, np.array(final_subjects))
        logger.info(f"Saved subject IDs to {subjects_path}")
        
        # Also save the behavioral data for the filtered subjects
        import pandas as pd
        behavioral_path = paths['behavioral_file']
        df = pd.read_csv(behavioral_path)
        mask = df['SubjectID' if 'SubjectID' in df.columns else df.columns[0]].astype(str).isin(final_subjects)
        filtered_df = df[mask]
        filtered_df.to_csv(paths['processed_dir'] / "filtered_behavioral.csv", index=False)
        logger.info(f"Saved filtered behavioral data to {paths['processed_dir'] / 'filtered_behavioral.csv'}")

        elapsed = time.time() - start_time
        logger.info(f"Pipeline completed successfully in {elapsed:.2f} seconds")
        return True

    except Exception as e:
        log_stage_error(logger, "Pipeline Execution", str(e))
        raise

if __name__ == "__main__":
    sys.exit(run_pipeline())
