"""
Main entry point for the research pipeline.

This script initializes the logging infrastructure and runs the core pipeline steps.
It serves as the integration point for data loading, preprocessing, modeling, and robustness checks.
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
from models import fit_primary_model, save_model_results
from robustness import run_all_robustness_checks, save_robustness_results
from binary_model import run_binary_model_pipeline

def main():
    """
    Execute the main research pipeline.
    
    Steps:
    1. Configure logging.
    2. Ensure required directories exist.
    3. Load data.
    4. Preprocess (impute, derive).
    5. Fit primary model.
    6. Run binary model (US2 prerequisite).
    7. Run all robustness checks (bootstrap, alpha sweep, covariates).
    8. Save all results.
    """
    # 1. Setup Logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting the political news exposure impact analysis pipeline.")
    
    try:
        # 2. Ensure directories
        ensure_dirs(["logs", "data/raw", "data/processed", "results"])
        logger.info("Directory structure verified.")
        
        # 3. Load Data
        logger.info("Attempting to load Project Implicit data...")
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
        
        # 5. Primary Model Fitting
        logger.info("Fitting primary linear regression model...")
        model_results = fit_primary_model(processed_df)
        
        if model_results:
            logger.info("Primary model fitting successful.")
            save_model_results(model_results)
            logger.info(f"Interaction term coefficient: {model_results.get('interaction_coef', 'N/A')}")
            logger.info(f"Interaction term p-value: {model_results.get('interaction_pval', 'N/A')}")
        else:
            logger.error("Primary model fitting failed to return results.")
            return

        # 6. Binary Model (US2 Prerequisite - T024b)
        logger.info("Running binary ideology model...")
        binary_results = run_binary_model_pipeline(processed_df)
        if binary_results:
            logger.info("Binary model completed.")
        else:
            logger.warning("Binary model returned no results.")

        # 7. Robustness Checks (US2 - T021, T022, T023 integration)
        logger.info("Starting robustness checks (Bootstrap, Alpha Sweep, Covariates)...")
        robustness_results = run_all_robustness_checks(processed_df)
        
        if robustness_results:
            logger.info("Robustness checks completed.")
            save_robustness_results(robustness_results)
            
            # Log key robustness metrics
            if 'bootstrap' in robustness_results:
                logger.info(f"Bootstrap CI for interaction: {robustness_results['bootstrap'].get('ci_95', 'N/A')}")
            if 'alpha_sweep' in robustness_results:
                logger.info(f"Alpha sweep results saved to results/alpha_sweep.csv")
            if 'covariate_adjustment' in robustness_results:
                logger.info(f"Covariate adjustment coefficient: {robustness_results['covariate_adjustment'].get('interaction_coef', 'N/A')}")
        else:
            logger.warning("Robustness checks returned no results.")
            
    except ValueError as e:
        logger.critical(f"Data or configuration error: {e}")
        raise
    except Exception as e:
        logger.exception(f"An unexpected error occurred during the pipeline: {e}")
        raise
    
    logger.info("Pipeline execution finished successfully.")

if __name__ == "__main__":
    main()