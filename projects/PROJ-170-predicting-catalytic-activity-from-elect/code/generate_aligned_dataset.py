import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from config import get_project_root, get_data_path, get_output_path
from preprocess import scale_features
from utils.validation import validate_schema

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_final_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validates that the DataFrame has the exact required columns and types.
    
    Required schema (per T020):
    - composition: string
    - surface_facet: string
    - energy_change: float (target)
    - d_band_center: float
    - adsorption_energy: float
    - (plus any other scaled descriptors from preprocessing)
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    
    # Define expected columns based on the pipeline description
    # Note: The exact list of descriptors depends on what was loaded and imputed.
    # We expect at least the core identifiers and the target.
    required_core_columns = [
        'composition', 
        'surface_facet', 
        'energy_change', 
        'd_band_center', 
        'adsorption_energy'
    ]
    
    # Check for required core columns
    missing_cols = [col for col in required_core_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for NaN in target variable
    if 'energy_change' in df.columns:
        nan_count = df['energy_change'].isna().sum()
        if nan_count > 0:
            errors.append(f"Target variable 'energy_change' contains {nan_count} NaN values.")
    
    # Check data types for numeric columns
    numeric_cols = ['energy_change', 'd_band_center', 'adsorption_energy']
    for col in numeric_cols:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"Column '{col}' is not numeric.")
    
    return len(errors) == 0, errors

def main():
    """
    Main entry point for T020: Generate data/processed/aligned_dataset.csv
    
    This script assumes:
    1. Raw data has been downloaded (T010).
    2. Preprocessing (alignment, exclusion, imputation, scaling) has been done in preprocess.py.
    3. The intermediate processed data (likely a parquet or csv in data/raw or a temporary state)
       exists and is ready to be finalized.
       
    Based on the task list, T019 (scaling) is in preprocess.py. 
    T020 is the final assembly and writing of the CSV.
    
    Strategy:
    - Re-run the necessary preprocessing steps to ensure consistency, OR
    - Load the intermediate result if T019 writes it to a specific location.
    
    Looking at the task list:
    T019: "Scale all numeric features..." (in preprocess.py)
    T020: "Generate data/processed/aligned_dataset.csv..."
    
    Since T019 is in `preprocess.py`, we assume `preprocess.py` has a function that 
    orchestrates the full pipeline up to scaling, or we call the individual steps 
    defined in `preprocess.py` here to assemble the final artifact.
    
    To be robust and self-contained for this task, we will:
    1. Load the raw data (or the aligned data if T014/15/17/19 wrote it).
    2. If no intermediate file exists, we assume the pipeline steps in `preprocess.py`
       need to be called sequentially to produce the final DataFrame.
       
    However, looking at the dependencies, T020 depends on T019. 
    If T019 is implemented in `preprocess.py` and writes to a temp location, we read it.
    If T019 just returns a DF, we need to call it.
    
    Let's assume the standard pattern for this project: 
    `preprocess.py` contains the logic, and `generate_aligned_dataset.py` orchestrates 
    the final write.
    
    We will attempt to load the data from the expected intermediate state.
    If T019 produced `data/raw/aligned_scaled.h5` or similar, we load it.
    If not, we re-run the logic from `preprocess.py` to generate it.
    
    Given the strict constraints, we will implement the full pipeline flow here 
    by calling the functions from `preprocess.py` to ensure the data is ready.
    """
    
    project_root = get_project_root()
    data_path = get_data_path()
    
    # Define paths
    raw_data_path = data_path / "raw" / "oc20_sample.h5"
    # We assume the intermediate processed data might be in a temp location or 
    # we need to regenerate it. Let's try to load the raw first.
    
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found at {raw_data_path}. "
                     "Please ensure T010 (download) has been completed successfully.")
        sys.exit(1)
    
    # Import the specific functions from preprocess
    # We need to orchestrate: Load -> Align -> Exclude -> Impute -> Scale -> Save
    from preprocess import (
        load_raw_oc20_data,
        align_entries,
        save_exclusion_log,
        retrieve_target_variable,
        compute_alignment_success_rate,
        save_alignment_metrics,
        impute_descriptors_knn,
        scale_features
    )
    
    logger.info("Starting generation of aligned_dataset.csv (T020)...")
    
    # 1. Load Raw Data
    logger.info(f"Loading raw data from {raw_data_path}")
    df_raw = load_raw_oc20_data(raw_data_path)
    
    # 2. Align Entries
    logger.info("Aligning entries...")
    # This function likely returns the aligned dataframe and exclusion info
    df_aligned, exclusion_log = align_entries(df_raw)
    
    # Save exclusion log (T014 requirement)
    exclusion_log_path = get_output_path() / "exclusion_log.json"
    save_exclusion_log(exclusion_log, exclusion_log_path)
    
    # 3. Retrieve Target
    logger.info("Retrieving target variable...")
    df_targeted = retrieve_target_variable(df_aligned)
    
    # 4. Impute Descriptors (T017, T018)
    logger.info("Imputing missing descriptors with KNN...")
    df_imputed, imputation_stats = impute_descriptors_knn(df_targeted)
    
    # Log stats if needed (T016/18)
    alignment_metrics = compute_alignment_success_rate(df_raw, df_imputed)
    save_alignment_metrics(alignment_metrics)
    
    # 5. Scale Features (T019)
    logger.info("Scaling features...")
    df_scaled = scale_features(df_imputed)
    
    # 6. Final Validation (T020)
    logger.info("Validating final schema...")
    is_valid, validation_errors = validate_final_schema(df_scaled)
    
    if not is_valid:
        logger.error(f"Final schema validation failed: {validation_errors}")
        sys.exit(1)
    
    # 7. Save to CSV
    output_dir = data_path / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "aligned_dataset.csv"
    
    logger.info(f"Saving final dataset to {output_file}")
    df_scaled.to_csv(output_file, index=False)
    
    logger.info(f"Successfully generated {output_file} with {len(df_scaled)} rows.")
    logger.info(f"Columns: {list(df_scaled.columns)}")
    
    return output_file

if __name__ == "__main__":
    main()
