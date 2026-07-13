import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import logging

# Import from existing API surface
from utils.logging import setup_logging, log_stage_start, log_stage_complete, log_stage_error
from config import get_paths, ensure_dirs
from data.download_hcp import main as download_main
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from modeling.train import main as train_main

def run_pipeline():
    """
    Orchestrate the full pipeline:
    1. Download raw data
    2. Preprocess time series
    3. Compute connectivity vectors (saves .npy to data/processed/)
    4. Train model (generates predictions.npy)
    """
    logger = setup_logging()
    logger.info("=== Starting Full Pipeline (main.py) ===")
    
    try:
        # 1. Download raw data
        log_stage_start("download", "Downloading HCP data and behavioral CSV")
        download_main()
        log_stage_complete("download", "Download complete")
        
        # 2. Preprocess time series (filters subjects, applies parcellation, nuisance regression, filtering)
        log_stage_start("preprocess", "Preprocessing time series for filtered subjects")
        preprocess_main()
        log_stage_complete("preprocess", "Preprocessing complete")
        
        # 3. Feature Engineering (computes connectivity vectors and saves .npy to data/processed/)
        log_stage_start("feature_engineering", "Computing connectivity vectors and saving .npy")
        feature_main()
        log_stage_complete("feature_engineering", "Feature engineering complete")
        
        # 4. Training (loads .npy, trains model, saves predictions.npy)
        log_stage_start("training", "Training model and generating predictions")
        train_main()
        log_stage_complete("training", "Training complete")
        
        logger.info("=== Full Pipeline Complete ===")
        
    except Exception as e:
        log_stage_error("pipeline", str(e))
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    run_pipeline()

if __name__ == "__main__":
    main()
