import sys
import os
from pathlib import Path
import pandas as pd
from code.config import ensure_dirs
from code.utils.logging import setup_logging, get_logger
from code.data.loader import load_dataset
from code.data.processor import process_dataset
from code.models.trainer import run_training_pipeline
from code.models.predictor import run_prediction_pipeline

def validate_alloy_family_counts(df: pd.DataFrame, logger) -> bool:
    """
    Validates that the dataset contains at least 50 samples per alloy family.
    Aborts the pipeline if this condition is not met (FR-008).
    
    Args:
        df: The processed DataFrame containing an 'alloy_family' column.
        logger: The configured logger instance.
        
    Returns:
        bool: True if validation passes, False otherwise.
    """
    if 'alloy_family' not in df.columns:
        logger.error("Validation failed: 'alloy_family' column not found in dataset.")
        return False
        
    family_counts = df['alloy_family'].value_counts()
    
    logger.info(f"Validating alloy family counts (min required: 50 per family)...")
    logger.info(f"Total families found: {len(family_counts)}")
    for family, count in family_counts.items():
        logger.info(f"  - {family}: {count} samples")
        
    if (family_counts < 50).any():
        families_below_threshold = family_counts[family_counts < 50].index.tolist()
        error_msg = (
            f"Validation failed (FR-008): The following alloy families have fewer than 50 samples: "
            f"{families_below_threshold}. Minimum required is 50 samples per family."
        )
        logger.error(error_msg)
        return False
        
    logger.info("Validation passed: All alloy families have >= 50 samples.")
    return True

def main():
    """
    Main entry point for the rolled metals texture prediction pipeline.
    Orchestrates: Load -> Validate -> Preprocess -> Train -> Predict -> Save
    """
    # Setup logging
    log_path = Path("data/pipeline.log")
    ensure_dirs([log_path.parent])
    logger = setup_logging(log_path=log_path)
    
    logger.info("Starting Rolled Metals Texture Prediction Pipeline")
    logger.info("=================================================")
    
    try:
        # 1. Load Data
        logger.info("Step 1: Loading dataset...")
        df_raw = load_dataset()
        if df_raw is None or df_raw.empty:
            logger.error("Dataset loading failed. Aborting.")
            sys.exit(1)
        
        # 2. Validate Data (FR-008)
        logger.info("Step 2: Validating data distribution...")
        # Note: Validation happens after loading but before heavy processing
        # to ensure we don't waste time on invalid data.
        if not validate_alloy_family_counts(df_raw, logger):
            logger.error("Pipeline aborted due to validation failure (FR-008).")
            sys.exit(1)
        
        # 3. Preprocess Data
        logger.info("Step 3: Preprocessing dataset...")
        df_processed = process_dataset(df_raw)
        if df_processed is None or df_processed.empty:
            logger.error("Data preprocessing resulted in an empty dataset. Aborting.")
            sys.exit(1)
        
        # 4. Train Model
        logger.info("Step 4: Training model...")
        model_path = Path("data/models/texture_model.pkl")
        ensure_dirs([model_path.parent])
        run_training_pipeline(df_processed, model_path, logger)
        
        # 5. Predictions
        logger.info("Step 5: Generating predictions...")
        run_prediction_pipeline(df_processed, model_path, logger)
        
        logger.info("Pipeline completed successfully.")
        
    except Exception as e:
        logger.exception(f"Pipeline failed with critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()