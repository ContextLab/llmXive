"""
Main entry point for the research pipeline.

This script initializes the logging infrastructure and runs the core pipeline steps.
It serves as the integration point for data loading, preprocessing, and modeling.
"""

import sys
from pathlib import Path

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from logging_config import setup_logging, get_logger
from config import ensure_dirs
from data_loader import load_project_implicit_data
from preprocessing import load_data, impute_mice, derive_variables
from models import fit_primary_model

def main():
    """
    Execute the main research pipeline.
    
    Steps:
    1. Configure logging.
    2. Ensure required directories exist.
    3. Load data.
    4. Preprocess (impute, derive).
    5. Fit model.
    6. Log results.
    """
    # 1. Setup Logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting the political news exposure impact analysis pipeline.")
    
    try:
        # 2. Ensure directories
        # We rely on ensure_dirs from config which was already implemented in T004
        ensure_dirs(["logs", "data/raw", "data/processed", "results"])
        logger.info("Directory structure verified.")
        
        # 3. Load Data
        logger.info("Attempting to load Project Implicit data...")
        # Note: This will raise ValueError if real data is not found, as per T038 constraints
        # For T008, we assume data availability or that the fetcher (T038) has run.
        # If T038 hasn't run, this will fail loudly as required.
        raw_df = load_project_implicit_data()
        
        if raw_df is None or raw_df.empty:
            logger.error("Data loading returned empty or None. Stopping.")
            return
        
        logger.info(f"Data loaded successfully. Shape: {raw_df.shape}")
        
        # 4. Preprocessing
        logger.info("Starting preprocessing (imputation and derivation)...")
        processed_df = load_data(raw_df)
        processed_df = impute_mice(processed_df)
        processed_df = derive_variables(processed_df)
        logger.info("Preprocessing complete.")
        
        # 5. Model Fitting
        logger.info("Fitting primary linear regression model...")
        model_results = fit_primary_model(processed_df)
        
        if model_results:
            logger.info("Model fitting successful.")
            logger.info(f"Interaction term coefficient: {model_results.get('interaction_coef', 'N/A')}")
            logger.info(f"Interaction term p-value: {model_results.get('interaction_pval', 'N/A')}")
        else:
            logger.error("Model fitting failed to return results.")
            
    except ValueError as e:
        logger.critical(f"Data or configuration error: {e}")
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during the pipeline: {e}")
        raise
    
    logger.info("Pipeline execution finished successfully.")

if __name__ == "__main__":
    main()
