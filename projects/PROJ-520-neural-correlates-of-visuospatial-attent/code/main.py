"""
Main entry point for the neural correlates pipeline.

This module orchestrates the execution of the entire pipeline, including
data download, preprocessing, feature extraction, and classification.
"""
import os
import sys
import logging
from pathlib import Path
from config import load_config, get_paths

# Import pipeline functions
from download_data import download_dataset
from preprocessing import preprocess_pipeline
from feature_extraction import run_extraction
from save_features import main as save_features_main
from classification import run_classification

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_download():
    """Run the data download task."""
    logger.info("Starting data download")
    config = load_config()
    paths = get_paths(config)
    
    success = download_dataset(paths['raw_data'])
    if success:
        logger.info("Data download completed successfully")
    else:
        logger.error("Data download failed")
    return success

def run_preprocess():
    """Run the preprocessing task."""
    logger.info("Starting preprocessing")
    config = load_config()
    paths = get_paths(config)
    
    success = preprocess_pipeline(paths['raw_data'], paths['processed_epochs'])
    if success:
        logger.info("Preprocessing completed successfully")
    else:
        logger.error("Preprocessing failed")
    return success

def run_features():
    """Run the feature extraction task."""
    logger.info("Starting feature extraction")
    config = load_config()
    paths = get_paths(config)
    
    # Run feature extraction
    success = run_extraction(paths['processed_epochs'], paths['tf_power'])
    if success:
        logger.info("Feature extraction completed successfully")
    else:
        logger.error("Feature extraction failed")
    return success

def run_classify():
    """Run the classification task."""
    logger.info("Starting classification")
    config = load_config()
    paths = get_paths(config)
    
    # First ensure features are saved
    save_features_main()
    
    success = run_classification(paths['features_matrix'], paths['final_results'])
    if success:
        logger.info("Classification completed successfully")
    else:
        logger.error("Classification failed")
    return success

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Neural Correlates Pipeline')
    parser.add_argument('--task', choices=['download', 'preprocess', 'features', 'classify', 'all'], 
                      default='all', help='Task to run')
    args = parser.parse_args()
    
    config = load_config()
    paths = get_paths(config)
    
    if args.task == 'download' or args.task == 'all':
        if not run_download():
            sys.exit(1)
    
    if args.task == 'preprocess' or args.task == 'all':
        if not run_preprocess():
            sys.exit(1)
    
    if args.task == 'features' or args.task == 'all':
        if not run_features():
            sys.exit(1)
    
    if args.task == 'classify' or args.task == 'all':
        if not run_classify():
            sys.exit(1)
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
