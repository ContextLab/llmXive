"""
Main entry point for the neural correlates analysis pipeline.

Orchestrates the full pipeline: download, preprocess, feature extraction, classification.
"""
import os
import sys
import logging
import argparse
import time
from pathlib import Path

from config import load_config, get_paths, ensure_directories
from logger import get_logger
from ci_limits import get_environment_report, enforce_limits

# Import pipeline modules
from download_data import main as download_main
from preprocessing import main as preprocess_main
from feature_extraction import main as features_main
from classification import main as classify_main
from streaming_loader import main as streaming_main

logger = get_logger(__name__)

def run_download(args):
    """Run the data download stage."""
    logger.info("Starting data download...")
    start_time = time.time()
    
    # Use streaming loader for large datasets
    if hasattr(args, 'stream') and args.stream:
        streaming_main()
    else:
        download_main()
        
    elapsed = time.time() - start_time
    logger.info(f"Data download completed in {elapsed:.1f}s")

def run_preprocess(args):
    """Run the preprocessing stage."""
    logger.info("Starting preprocessing...")
    start_time = time.time()
    
    preprocess_main()
    
    elapsed = time.time() - start_time
    logger.info(f"Preprocessing completed in {elapsed:.1f}s")

def run_features(args):
    """Run the feature extraction stage."""
    logger.info("Starting feature extraction...")
    start_time = time.time()
    
    features_main()
    
    elapsed = time.time() - start_time
    logger.info(f"Feature extraction completed in {elapsed:.1f}s")

def run_classify(args):
    """Run the classification stage."""
    logger.info("Starting classification...")
    start_time = time.time()
    
    classify_main()
    
    elapsed = time.time() - start_time
    logger.info(f"Classification completed in {elapsed:.1f}s")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Neural Correlates Analysis Pipeline")
    parser.add_argument('--task', type=str, choices=['download', 'preprocess', 'features', 'classify', 'all'], 
                      default='all', help='Task to run')
    parser.add_argument('--dataset', type=str, default='ds0001171', help='OpenNeuro dataset ID')
    parser.add_argument('--config', type=str, default=None, help='Path to config file')
    parser.add_argument('--stream', action='store_true', help='Use streaming mode for large datasets')
    parser.add_argument('--timing', action='store_true', help='Report timing information')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('pipeline.log')
        ]
    )
    
    logger.info("=== Neural Correlates Analysis Pipeline ===")
    
    # Check environment limits
    is_valid, message = enforce_limits()
    if not is_valid:
        logger.error(f"Environment check failed: {message}")
        sys.exit(1)
    logger.info(f"Environment check passed: {message}")
    
    # Load configuration
    config = load_config(args.config) if args.config else load_config()
    config['DATASET_ID'] = args.dataset
    
    # Ensure directories exist
    ensure_directories(config)
    
    # Run selected task(s)
    start_time = time.time()
    
    try:
        if args.task in ['download', 'all']:
            run_download(args)
            
        if args.task in ['preprocess', 'all']:
            run_preprocess(args)
            
        if args.task in ['features', 'all']:
            run_features(args)
            
        if args.task in ['classify', 'all']:
            run_classify(args)
            
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)
        
    total_time = time.time() - start_time
    logger.info(f"=== Pipeline completed in {total_time:.1f}s ===")
    
    if args.timing:
        logger.info(f"Total execution time: {total_time:.1f}s")

if __name__ == "__main__":
    main()
