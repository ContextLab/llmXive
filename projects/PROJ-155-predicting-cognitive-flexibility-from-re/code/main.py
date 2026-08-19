import os
import sys
import logging
import argparse
from typing import Optional, Dict, Any
from code.config import set_seed, get_config
from code.data.download import run_download_pipeline
from code.data.preprocess import run_preprocessing_pipeline
from code.data.merge import run_merge_pipeline
from code.utils.motion import run_motion_filtering_pipeline
from code.data.behavioral_validator import run_behavioral_validation_pipeline
from code.data.paths import get_raw_path, get_processed_path, ensure_dir
from code.utils.exclusion_stats import run_success_rate_pipeline
from code.utils.logging import init_logging

logger = logging.getLogger(__name__)

def run_pipeline(args: Optional[argparse.Namespace] = None) -> None:
    """
    Execute the full data processing pipeline.
    
    This pipeline runs in the following order:
    1. Download HCP data
    2. Preprocess (parcellation)
    3. Merge neuroimaging and behavioral data
    4. Filter by motion (Mean FD > 0.2)
    5. Filter by missing behavioral scores (T017)
    6. Calculate exclusion statistics (T015a)
    7. Validate final results (T016)
    
    Args:
        args: Command line arguments (optional).
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Run the cognitive flexibility prediction pipeline.")
        parser.add_argument("--seed", type=int, default=42, help="Random seed")
        parser.add_argument("--subjects", type=str, nargs="+", help="Specific subject IDs to process")
        args = parser.parse_args()

    set_seed(args.seed)
    config = get_config()
    init_logging()

    logger.info("=" * 60)
    logger.info("Starting Cognitive Flexibility Prediction Pipeline")
    logger.info("=" * 60)

    # 1. Download Data
    logger.info("Step 1: Downloading HCP data...")
    raw_path = get_raw_path()
    ensure_dir(raw_path)
    # Assuming run_download_pipeline handles the manifest and subject filtering
    run_download_pipeline(subject_ids=args.subjects)

    # 2. Preprocess
    logger.info("Step 2: Preprocessing fMRI data...")
    run_preprocessing_pipeline()

    # 3. Merge
    logger.info("Step 3: Merging neuroimaging and behavioral data...")
    merged_df = run_merge_pipeline()

    # 4. Motion Filtering (T015)
    logger.info("Step 4: Applying motion exclusion (Mean FD > 0.2)...")
    motion_filtered_df = run_motion_filtering_pipeline(merged_df)

    # 5. Behavioral Score Filtering (T017)
    logger.info("Step 5: Filtering missing behavioral scores...")
    processed_path = get_processed_path()
    ensure_dir(processed_path)
    
    # Assuming the merged data has a column 'Flexibility_Score'
    # We pass the behavioral CSV path if needed for reference, but the DF is already merged
    # The function will identify missing scores in the DF, log them, and return the filtered DF
    final_df = run_behavioral_validation_pipeline(
        motion_filtered_df, 
        behavioral_csv_path=os.path.join(raw_path, "hcp_behavioral.csv"), 
        score_column="Flexibility_Score"
    )

    # 6. Save Final Results (T016)
    logger.info("Step 6: Saving final results...")
    output_path = os.path.join(processed_path, "final_results.csv")
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved final results to {output_path}")

    # 7. Calculate Exclusion Stats (T015a)
    logger.info("Step 7: Calculating exclusion statistics...")
    run_success_rate_pipeline()

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully.")
    logger.info("=" * 60)

def main():
    run_pipeline()

if __name__ == "__main__":
    main()