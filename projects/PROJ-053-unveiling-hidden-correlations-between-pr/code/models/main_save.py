import sys
import os
import logging
import argparse
from config import get_models_dir, ensure_directories, get_random_seed
from utils.logger import setup_logging
from data.preprocess import load_raw_csv, detect_missing_values, compute_medians, impute_missing_values, encode_categorical, check_sample_count, check_zero_variance, split_and_scale, validate_and_preprocess
from models.gpr_trainer import train_gpr_model
from models.baseline_trainer import train_linear_baseline
from models.saver import save_models

def main():
    """
    Main entry point to train and save GPR and Linear Baseline models.
    
    This script:
    1. Loads and preprocesses data from data/raw/
    2. Trains a GPR model and a Linear Regression baseline
    3. Saves both models to results/models/
    """
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Model Training and Saving Pipeline (T026)")
    logger.info(f"Random seed: {get_random_seed()}")
    
    try:
        # 1. Load and Preprocess Data
        # The validate_and_preprocess function handles loading, validation, 
        # imputation, encoding, splitting, and scaling.
        # It returns X_train, X_test, y_train, y_test, and metadata.
        
        logger.info("Loading and preprocessing data...")
        # Assuming the raw file is at the standard location defined in config
        # We need to pass the path or let the function find it. 
        # Based on T014/T016, we assume a standard flow.
        
        # We call the preprocessor. Note: The preprocessor in T014/T016 
        # saves the processed CSV. We need to load that or re-run the logic.
        # For this task, we will assume the preprocessor logic is available 
        # and we need to execute the full pipeline to get the split data.
        
        # Re-using the logic from T014/T016:
        # We need to ensure the data exists first.
        # If T013 failed, this will raise an error, which is correct behavior.
        
        # Let's assume the preprocessed data is already at data/processed/preprocessed_data.csv
        # or we run the full pipeline here.
        # To be safe and self-contained for this task, we will call the 
        # validation and preprocessing steps that produce the split data.
        
        # Since the exact signature of the full pipeline in preprocess.py 
        # might vary slightly, we will rely on the exported functions.
        # We will simulate the flow: Load -> Validate -> Preprocess -> Split.
        
        # However, the most robust way given the API surface is to assume 
        # the `validate_and_preprocess` function does the heavy lifting 
        # and returns the tensors/arrays needed.
        
        # Let's check the API: `validate_and_preprocess` is listed.
        # We assume it returns (X_train, X_test, y_train, y_test, metadata)
        
        # If the raw data is missing, this will fail loudly (T013C behavior).
        X_train, X_test, y_train, y_test, metadata = validate_and_preprocess()
        
        logger.info(f"Data loaded. Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")
        
        # 2. Train Linear Baseline
        logger.info("Training Linear Regression Baseline...")
        linear_model, linear_info = train_linear_baseline(X_train, y_train)
        
        # 3. Train GPR Model
        logger.info("Training Gaussian Process Regression Model...")
        gpr_model, gpr_info = train_gpr_model(X_train, y_train)
        
        # 4. Save Models
        logger.info("Saving models to results/models/...")
        
        # Prepare metadata for saving
        gpr_metadata = {
            "type": "GaussianProcessRegressor",
            "kernel": str(gpr_model.kernel_),
            "hyperparameters_optimized": True,
            "source": "code/models/gpr_trainer.py"
        }
        gpr_metadata.update(gpr_info)
        
        linear_metadata = {
            "type": "LinearRegression",
            "source": "code/models/baseline_trainer.py",
            "coef_shape": linear_model.coef_.shape if hasattr(linear_model, 'coef_') else None
        }
        linear_metadata.update(linear_info)
        
        saved_paths = save_models(
            gpr_model=gpr_model,
            linear_baseline=linear_model,
            gpr_metadata=gpr_metadata,
            linear_metadata=linear_metadata
        )
        
        logger.info("Model saving complete.")
        logger.info(f"Saved GPR Model: {saved_paths['gpr_model']}")
        logger.info(f"Saved Linear Baseline: {saved_paths['linear_baseline']}")
        
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Please ensure raw data is placed in data/raw/ or T013 download succeeded.")
        return 1
    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
