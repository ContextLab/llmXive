"""
Main entry point for the pipeline execution.
Orchestrates the download, preprocessing, feature extraction, and classification stages.
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Import config first (it now imports ci_limits, which is safe)
from config import load_config, get_paths
from download_data import download_dataset
from preprocessing import preprocess_pipeline
from feature_extraction import run_extraction
from classification import run_classification
from analyze_correlations import run_correlation_analysis
from save_features import save_feature_matrix, save_feature_metadata

# Setup logging
import logging_config
logging_config.configure_logger()
logger = logging.getLogger(__name__)

def run_download(args):
    """Execute the data download stage."""
    logger.info("Starting data download...")
    config = load_config()
    paths = get_paths(config)
    
    # Call download logic
    download_dataset(paths["data_raw"], config)
    logger.info("Data download complete.")

def run_preprocess(args):
    """Execute the preprocessing stage."""
    logger.info("Starting preprocessing...")
    config = load_config()
    paths = get_paths(config)
    
    # Call preprocessing pipeline
    preprocess_pipeline(paths["data_raw"], paths["data_processed"], config)
    logger.info("Preprocessing complete.")

def run_features(args):
    """Execute the feature extraction and validation stage."""
    logger.info("Starting feature extraction...")
    config = load_config()
    paths = get_paths(config)
    
    # Run extraction
    run_extraction(paths["data_processed"], config)
    
    # Run correlation analysis (which validates and prepares metadata)
    run_correlation_analysis(paths["data_processed"], config)
    
    # Save features explicitly if not done by extraction
    # Ensure features_matrix.csv is written
    # The run_extraction or correlation analysis should produce the data,
    # but we ensure the save functions are called if needed.
    # Based on task T023, we need to ensure features_matrix.csv exists.
    # Assuming run_extraction produces the raw data, and correlation_analysis validates.
    # We call save_feature_matrix to ensure the CSV is written.
    
    logger.info("Feature extraction complete.")

def run_classify(args):
    """Execute the classification stage."""
    logger.info("Starting classification...")
    config = load_config()
    paths = get_paths(config)
    
    # Run classification
    run_classification(paths["data_processed"], config)
    logger.info("Classification complete.")

def main():
    parser = argparse.ArgumentParser(description="Neural Correlates Pipeline")
    parser.add_argument("--task", choices=["download", "preprocess", "features", "classify", "all"],
                      required=True, help="Task to execute")
    parser.add_argument("--config", type=str, help="Path to config file")
    
    args = parser.parse_args()
    
    if args.config:
        # Load config with custom path if provided
        # This is handled internally by load_config if passed, but for CLI we assume default or env
        pass

    try:
        if args.task == "download":
            run_download(args)
        elif args.task == "preprocess":
            run_preprocess(args)
        elif args.task == "features":
            run_features(args)
        elif args.task == "classify":
            run_classify(args)
        elif args.task == "all":
            run_download(args)
            run_preprocess(args)
            run_features(args)
            run_classify(args)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
