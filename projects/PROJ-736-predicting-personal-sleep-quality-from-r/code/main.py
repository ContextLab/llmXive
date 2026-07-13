"""Main orchestration script for the sleep quality prediction pipeline.

This script orchestrates the full pipeline:
1. Download and filter raw data
2. Preprocess time series
3. Compute connectivity vectors
4. Train model and save predictions
5. Save connectivity vectors as .npy files
"""
import os
import sys
import json
import time
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, get_logger
from data.download_hcp import main as download_main, filter_subjects, load_behavioral_data
from data.preprocess import main as preprocess_main
from data.feature_engineering import main as feature_main
from modeling.train import main as train_main

def run_pipeline() -> bool:
    """
    Run the full data pipeline: download, preprocess, feature engineering, train.
    
    Returns:
        True if successful, False otherwise.
    """
    logger = get_logger()
    log_stage_start("full_pipeline")
    
    try:
        paths = get_paths()
        
        # Step 1: Download and filter subjects
        log_stage_start("Download and Filter")
        if not download_main():
            raise RuntimeError("Download and filter step failed")
        log_stage_complete("Download and Filter")
        
        # Step 2: Preprocess data (will use filtered subjects)
        # Note: Preprocessing requires CIFTI files. If they are not available,
        # this step will fail. The pipeline is designed to fail loudly if real data
        # is missing, rather than faking results.
        log_stage_start("Preprocessing")
        if not preprocess_main():
            raise RuntimeError("Preprocessing step failed")
        log_stage_complete("Preprocessing")
        
        # Step 3: Feature engineering
        # This step computes connectivity vectors and saves them as .npy files
        # to data/processed/
        log_stage_start("Feature Engineering")
        if not feature_main():
            raise RuntimeError("Feature engineering step failed")
        log_stage_complete("Feature Engineering")
        
        # Step 4: Train model
        # This step also saves predictions to data/processed/predictions.npy
        log_stage_start("Training")
        if not train_main():
            raise RuntimeError("Training step failed")
        log_stage_complete("Training")
        
        # Verify outputs
        processed_dir = Path(paths["processed_dir"])
        
        # Check for connectivity vectors
        connectivity_files = list(processed_dir.glob("*_connectivity.npy"))
        if len(connectivity_files) == 0:
            log_stage_error("full_pipeline", "No connectivity vectors found")
            return False
        
        # Check for predictions file
        predictions_file = processed_dir / "predictions.npy"
        if not predictions_file.exists():
            log_stage_error("full_pipeline", "Predictions file not found")
            return False
        
        log_stage_complete("full_pipeline")
        return True
        
    except Exception as e:
        log_stage_error("full_pipeline", error=str(e))
        logger.error(f"Pipeline failed: {str(e)}")
        return False

def main() -> bool:
    """Main entry point."""
    return run_pipeline()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)