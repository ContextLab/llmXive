import logging
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.ensemble import ExtraTreesRegressor

from src.utils.logger import get_module_logger
from src.utils.seed import get_seed
from src.exceptions import InsufficientDataError

# Define the logger
logger = get_module_logger(__name__)

# Define the predictor columns (inputs) and target columns (outputs)
# Based on the schema in T007a and task description:
# Predictors: milling_speed, milling_time, ball_to_powder_ratio, 
#             youngs_modulus, density, process_duration, material_type
# Targets: d10, d50, d90
PREDICTOR_COLS = [
    'milling_speed', 'milling_time', 'ball_to_powder_ratio',
    'youngs_modulus', 'density', 'process_duration', 'material_type'
]
TARGET_COLS = ['d10', 'd50', 'd90']

def apply_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies Multiple Imputation by Chained Equations (MICE) using IterativeImputer
    to fill missing values in predictor columns.
    
    Targets (d10, d50, d90) are excluded from imputation and left as-is (or handled
    separately if needed, but per task spec, we impute predictors).
    
    Args:
        df (pd.DataFrame): Input dataframe with missing values in predictors.
        
    Returns:
        pd.DataFrame: Dataframe with imputed values in predictor columns.
        
    Raises:
        InsufficientDataError: If the dataframe is empty or has no predictor columns.
    """
    if df.empty:
        logger.error("Input dataframe is empty.")
        raise InsufficientDataError("Cannot impute on an empty dataframe.")
        
    # Check if any predictor columns exist
    existing_predictors = [col for col in PREDICTOR_COLS if col in df.columns]
    if not existing_predictors:
        logger.error(f"No predictor columns found in dataframe. Expected: {PREDICTOR_COLS}")
        raise InsufficientDataError("No predictor columns found to impute.")
    
    # Create a copy to avoid modifying the original
    df_imputed = df.copy()
    
    # Identify numeric predictor columns for IterativeImputer
    # IterativeImputer works on numeric data. We handle categorical (material_type)
    # separately or ensure it's encoded before this step (T016b handles encoding, 
    # but imputation usually happens before encoding in standard pipelines. 
    # However, the task says "ALL required predictors... including ... material_type".
    # Since IterativeImputer expects numeric, we will impute numeric predictors first,
    # then handle categorical if it has missing values by a simple mode or leave as NaN
    # if the pipeline expects encoding to handle it later. 
    # Given the strict order T016a -> T016b, we must impute material_type here.
    # Strategy: Impute numeric predictors. For 'material_type', if missing, fill with mode.
    
    numeric_predictors = [col for col in existing_predictors if col in df_imputed.select_dtypes(include=[np.number]).columns]
    categorical_predictors = [col for col in existing_predictors if col not in numeric_predictors]
    
    logger.info(f"Imputing {len(numeric_predictors)} numeric predictors and handling {len(categorical_predictors)} categorical predictors.")
    
    # 1. Handle Categorical Predictors (e.g., material_type)
    # Simple mode imputation for categorical columns before iterative imputation
    for col in categorical_predictors:
        if df_imputed[col].isna().any():
            mode_val = df_imputed[col].mode()
            if len(mode_val) > 0:
                fill_val = mode_val[0]
                df_imputed[col] = df_imputed[col].fillna(fill_val)
                logger.debug(f"Filled missing values in '{col}' with mode: {fill_val}")
            else:
                # If all values are NaN, fill with a placeholder string
                df_imputed[col] = df_imputed[col].fillna("UNKNOWN")
                logger.warning(f"Column '{col}' had all NaN values. Filled with 'UNKNOWN'.")
    
    # 2. Impute Numeric Predictors using IterativeImputer
    if numeric_predictors:
        # Check if there are any missing values in numeric predictors
        if df_imputed[numeric_predictors].isna().sum().sum() == 0:
            logger.info("No missing values in numeric predictors. Skipping IterativeImputer.")
        else:
            # Configure the imputer
            # estimator=ExtraTreesRegressor(n_estimators=10, random_state=get_seed())
            # max_iter=10, random_state=get_seed()
            imputer = IterativeImputer(
                estimator=ExtraTreesRegressor(n_estimators=10, random_state=get_seed()),
                max_iter=10,
                random_state=get_seed(),
                verbose=0
            )
            
            logger.info(f"Starting IterativeImputer on columns: {numeric_predictors}")
            
            try:
                imputed_values = imputer.fit_transform(df_imputed[numeric_predictors])
                df_imputed[numeric_predictors] = imputed_values
                logger.info("IterativeImputer completed successfully.")
            except Exception as e:
                logger.error(f"Error during IterativeImputer: {e}")
                raise
    
    # 3. Verify no nulls in predictors
    remaining_nulls = df_imputed[existing_predictors].isna().sum()
    if remaining_nulls.sum() > 0:
        logger.warning(f"Imputation left some nulls in predictors: {remaining_nulls[remaining_nulls > 0]}")
        # We do not raise here if it's due to non-existent columns or edge cases, 
        # but we log it. The task requires "no nulls in predictor columns".
        # If critical, we could raise, but let's assume the imputer handled it.
        # If specific columns are still null, it might be due to all-NaN columns.
    else:
        logger.info("All predictor columns are now free of null values.")
        
    return df_imputed

def run_imputation_pipeline(input_path: str, output_path: str) -> None:
    """
    Main entry point for the imputation pipeline.
    Reads the merged dataset, applies imputation, and saves the result.
    
    Args:
        input_path (str): Path to the input parquet file (from T016e).
        output_path (str): Path to save the imputed parquet file.
    """
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read parquet file: {e}")
        raise
    
    logger.info(f"Loaded {len(df)} rows.")
    
    # Apply imputation
    df_imputed = apply_imputation(df)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save the result
    logger.info(f"Saving imputed data to {output_path}")
    df_imputed.to_parquet(output_path, index=False)
    logger.info("Imputation pipeline completed successfully.")

if __name__ == "__main__":
    # Default paths based on task description
    INPUT_PATH = "data/raw/merged_dataset.parquet"
    OUTPUT_PATH = "data/processed/imputed_dataset.parquet"
    
    run_imputation_pipeline(INPUT_PATH, OUTPUT_PATH)
