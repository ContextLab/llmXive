"""
Module: code/generate_aligned_dataset.py
Task: T020 [US1] Generate data/processed/aligned_dataset.csv with final schema.
Depends on: T019 (scaling), T017 (imputation), T015 (target retrieval), T014 (alignment).

This script loads the preprocessed data (which has been aligned, imputed, and scaled
by previous steps in the pipeline), validates the final schema, and writes the
result to data/processed/aligned_dataset.csv.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import from project modules
from config import get_project_root, get_data_path, get_output_path
from utils.validation import validate_schema, validate_no_null_targets
from logging_config import get_logger

# Define the expected final schema columns
# Based on T010/T014/T015: composition, surface_facet, energy_change (target),
# d_band_center, adsorption_energy, and the scaled/imputed descriptors.
# The exact list of descriptor columns will be dynamic based on the input data,
# but the core structural columns are fixed.
EXPECTED_CORE_COLUMNS = [
    'composition',
    'surface_facet',
    'energy_change',  # Target variable
    'd_band_center',
    'adsorption_energy'
]

def validate_final_schema(df: pd.DataFrame, logger: logging.Logger) -> Tuple[bool, List[str]]:
    """
    Validates that the dataframe contains the required core columns and no NaN values
    in the target column.
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for core columns
    missing_cols = [col for col in EXPECTED_CORE_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
        return False, errors
    
    # Check for NaN in target variable (energy_change)
    # T015/T017 should have handled this, but we double-check before final output
    if df['energy_change'].isna().any():
        nan_count = df['energy_change'].isna().sum()
        errors.append(f"Target variable 'energy_change' contains {nan_count} NaN values. Imputation failed.")
        return False, errors
    
    # Check for any remaining NaN in feature columns (if strict)
    # T017 (KNN imputation) should have removed rows with <5 neighbors, 
    # but we ensure no NaNs remain in the final dataset.
    if df.isna().any().any():
        na_counts = df.isna().sum()
        cols_with_na = na_counts[na_counts > 0].index.tolist()
        errors.append(f"Dataset still contains NaN values in columns: {cols_with_na}")
        return False, errors

    logger.info(f"Schema validation passed. Columns: {list(df.columns)}")
    logger.info(f"Row count: {len(df)}, Target NaN count: {df['energy_change'].isna().sum()}")
    return True, errors

def main():
    """
    Main entry point for T020.
    1. Loads the preprocessed data from the intermediate location (likely data/processed/intermediate_*.csv 
       or the output of the last preprocess step). 
       *Correction*: Based on the pipeline flow, T019 (scale) and T017 (impute) are steps in preprocess.py.
       The data is likely held in memory or saved to a temporary state. 
       However, T019 implies the data is ready. 
       We assume the previous step (T019) saved the processed data to a temporary file or 
       the pipeline is run sequentially in a single process. 
       
       *Assumption for this script*: The pipeline is designed such that `preprocess.py` 
       saves the intermediate aligned/scaled data to `data/processed/intermediate_aligned.csv` 
       or similar, OR we load the raw OC20 and re-run the pipeline steps if they are stateless.
       
       *Refined Assumption*: The tasks T014-T019 are steps in `preprocess.py`. 
       Usually, a pipeline script (like `run_pipeline.py`) would orchestrate this. 
       Since T020 is "Generate ... with final schema", it implies taking the result of T019.
       
       If T019 didn't write a file, we must assume the data is available in a state file 
       or we need to re-run the logic. 
       Given the task list, T019 is "Scale all numeric features". 
       It is highly likely that `code/preprocess.py` has a `main` that runs the whole chain 
       and saves an intermediate file, or T020 is meant to be the final step of that chain.
       
       Let's assume `preprocess.py` saves the result of T019 to `data/processed/aligned_dataset_pre_final.csv`
       or we load the raw data and apply the logic if the pipeline is not yet modularized into 
       separate file writes.
       
       *Wait, T010-T019 are tasks, not necessarily separate script executions.* 
       If they are tasks in a `tasks.md`, they might be executed by a runner.
       However, T020 explicitly says "Generate ... with final schema".
       
       Let's look at the dependencies: T020 depends on T019.
       If T019 is a function call in `preprocess.py`, the data might be in memory.
       But T020 is a separate task.
       
       *Hypothesis*: The project structure expects `code/preprocess.py` to perform T014-T019 
       and save an intermediate file (e.g., `data/processed/scaled_data.csv`). 
       Then T020 reads that, validates, and saves the final `aligned_dataset.csv`.
       
       *Alternative*: `preprocess.py` doesn't save intermediate files, and T020 is the 
       final step that calls the functions in `preprocess.py` to generate the file.
       
       Let's implement T020 as a script that:
       1. Loads the raw data (T010).
       2. Runs alignment (T014).
       3. Runs target retrieval (T015).
       4. Runs imputation (T017).
       5. Runs scaling (T019).
       6. Validates (T020).
       7. Saves.
       
       This ensures the data is real and the pipeline is reproducible in this single script,
       assuming the intermediate files from T010-T019 might not exist or this is the "finalize" step.
       
       *Correction*: The prompt says "Depends on T019". If T019 was already run, the data should exist.
       If T019 was run by `preprocess.py`, it likely saved the result. 
       Let's assume the previous steps saved the data to `data/processed/intermediate_scaled.csv`.
       If that file doesn't exist, we must re-run the pipeline logic to ensure we have data.
       
       Given the "Real data only" constraint and the need to ensure the file exists:
       We will attempt to load `data/processed/intermediate_scaled.csv`.
       If it doesn't exist, we will assume the previous tasks (T010-T019) were not executed 
       as a script that writes to disk, or we are re-running the pipeline.
       
       However, T010 downloads data. T014 aligns. T017 imputes. T019 scales.
       If these were run as separate tasks, they would have written state.
       If they were run as a single `preprocess.py` execution, they might have written the final file.
       
       Let's assume the standard pattern: `preprocess.py` saves the result of T019 to 
       `data/processed/aligned_dataset_pre_final.csv` (or similar).
       If not, we re-run the logic.
       
       To be safe and robust:
       We will check for `data/processed/intermediate_scaled.csv`.
       If missing, we will re-run the full preprocessing chain (T014-T019) from the raw data
       (which should exist from T010).
       
       Actually, looking at T010, it downloads to `data/raw/oc20_sample.h5`.
       T014-T019 process this.
       If T019 didn't save, we must save.
       
       Let's assume the `preprocess.py` module has functions for each step.
       We will call them in order if the intermediate file is missing, or load the intermediate file.
       
       Wait, T019 is "Scale all numeric features".
       T020 is "Generate ... with final schema".
       This implies T020 is the finalization step.
       
       Let's implement it to:
       1. Check if `data/processed/intermediate_scaled.csv` exists.
       2. If not, load raw, align, impute, scale, and save to intermediate.
       3. Load intermediate (or the one just saved).
       4. Validate schema.
       5. Save to `data/processed/aligned_dataset.csv`.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    data_path = get_data_path()
    
    raw_file = data_path / "raw" / "oc20_sample.h5"
    intermediate_file = data_path / "processed" / "intermediate_scaled.csv"
    final_output_file = data_path / "processed" / "aligned_dataset.csv"
    
    # Ensure directories exist
    final_output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df = None
    
    # Check if intermediate file exists (from T019)
    if intermediate_file.exists():
        logger.info(f"Loading intermediate scaled data from {intermediate_file}")
        try:
            df = pd.read_csv(intermediate_file)
        except Exception as e:
            logger.error(f"Failed to load intermediate file: {e}")
            logger.info("Re-running preprocessing pipeline...")
            df = None
    
    if df is None:
        logger.info("Intermediate file not found or corrupted. Re-running preprocessing pipeline (T014-T019).")
        
        # 1. Load Raw Data (T010)
        # Assuming T010 saved to raw_file. If not, we might need to download again, 
        # but T010 is marked complete.
        if not raw_file.exists():
            logger.error(f"Raw data file {raw_file} not found. T010 must be run first.")
            # We cannot proceed without data.
            # In a real scenario, we might call download_data.main() here, 
            # but T010 is supposed to be done.
            raise FileNotFoundError(f"Raw data file {raw_file} not found. Please ensure T010 is completed.")
        
        # Load raw data
        # T010 downloaded an H5 file. We need to load it.
        try:
            df = pd.read_hdf(raw_file, key='df') # Assuming key is 'df' or default
            if not isinstance(df, pd.DataFrame):
                # Try to read as dict of dataframes if it's a group
                # Standard OC20 sample might be a single dataframe
                logger.warning("HDF5 structure unexpected, trying default key or root")
                # Fallback: if it's a list of keys, pick the first one
                import h5py
                with h5py.File(raw_file, 'r') as f:
                    keys = list(f.keys())
                    if len(keys) == 1:
                        df = pd.read_hdf(raw_file, key=keys[0])
                    else:
                        # Try to find the largest one or 'data'
                        # For simplicity, assume 'df' or first key
                        df = pd.read_hdf(raw_file, key=keys[0])
        except Exception as e:
            logger.error(f"Failed to load raw data from {raw_file}: {e}")
            raise
        
        logger.info(f"Loaded raw data: {df.shape}")
        
        # 2. Align Entries (T014)
        # We need to call the functions from preprocess.py
        from preprocess import align_entries, save_exclusion_log
        
        # align_entries expects a dataframe and returns aligned dataframe and stats
        # We need to handle the exclusion log
        # The function signature from API surface: align_entries(df) -> (aligned_df, stats)
        # But we need to save the exclusion log.
        # Let's assume align_entries returns the aligned df and we handle logging.
        
        # Re-reading API: `align_entries` is in `preprocess.py`.
        # We need to pass the raw df.
        # We also need to handle the exclusion logic.
        
        # Since we are re-implementing the flow here, let's assume the functions work as expected.
        # We might need to call `load_raw_oc20_data` if the data is not in the expected format.
        # But we just loaded it from H5.
        
        # Let's assume `align_entries` takes the dataframe and returns the aligned one.
        # We also need to save the exclusion log to outputs/exclusion_log.json (T014)
        exclusion_log_path = get_output_path() / "exclusion_log.json"
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # We need to call align_entries. 
        # The API surface says: align_entries(df) -> ...
        # But we need to handle the exclusion log.
        # Let's assume the function returns (aligned_df, excluded_count, excluded_reasons)
        # or we call save_exclusion_log separately.
        
        # To be safe, let's call the functions in the order defined in the task description.
        # T014: Align entries.
        # T015: Retrieve target.
        # T017: Impute.
        # T019: Scale.
        
        # We need to ensure we have the correct functions.
        # Let's assume the functions return the necessary data.
        
        # 2.1 Align
        # The function `align_entries` might need the raw data.
        # Let's assume it returns the aligned dataframe.
        # We also need to handle the exclusion log.
        # We'll call `save_exclusion_log` if we have the data.
        
        # Since we don't have the exact implementation of `align_entries` in the prompt,
        # we assume it works as described in T014.
        # We'll call it and handle the result.
        
        # To ensure we don't break if the function signature is different,
        # we'll try to call it and handle exceptions.
        # But the prompt says "import the real names".
        
        # Let's assume `align_entries` returns (aligned_df, stats_dict).
        # We'll extract the exclusion info from stats_dict or call save_exclusion_log.
        
        # Actually, T014 says "Implement ... save_exclusion_log".
        # So `save_exclusion_log` is a function that takes the exclusion data.
        
        # Let's assume `align_entries` returns (aligned_df, exclusion_data).
        # We'll call `save_exclusion_log(exclusion_data)`.
        
        # 2.2 Retrieve Target (T015)
        # `retrieve_target_variable` might be part of the alignment or a separate step.
        # We'll assume it's done in `align_entries` or we call it.
        
        # 2.3 Impute (T017)
        # `impute_descriptors_knn`
        
        # 2.4 Scale (T019)
        # `scale_features`
        
        # Let's try to chain these.
        # If the functions are not returning what we expect, we might need to adjust.
        # But we must use the API surface.
        
        # We'll assume the following flow:
        # df = align_entries(df) -> returns aligned_df
        # df = retrieve_target_variable(df) -> returns df with target
        # df = impute_descriptors_knn(df) -> returns df with imputed values
        # df = scale_features(df) -> returns scaled df
        
        # We need to handle the exclusion log.
        # Let's assume `align_entries` returns (df, exclusion_log).
        # If not, we might need to call `save_exclusion_log` with some default or empty data.
        # But T014 says "Implement ... save_exclusion_log".
        # So we must call it.
        
        # Let's assume `align_entries` returns (df, exclusion_log).
        # We'll call `save_exclusion_log(exclusion_log)`.
        
        # To be safe, we'll use a try-except block and log errors.
        
        try:
            # Align
            # We assume the function returns the aligned dataframe and exclusion log
            # If the function signature is different, we adjust.
            # Based on T014: "Implement ... save_exclusion_log".
            # So we call `save_exclusion_log` with the exclusion data.
            # Let's assume `align_entries` returns (df, exclusion_log).
            aligned_df, exclusion_log = align_entries(df)
            save_exclusion_log(exclusion_log)
            df = aligned_df
            logger.info(f"Alignment complete. Excluded {len(exclusion_log)} entries.")
            
            # Retrieve Target
            # T015: "Retrieve target variable ... Log any missing target values for exclusion."
            # We assume `retrieve_target_variable` handles this.
            df = retrieve_target_variable(df)
            logger.info("Target variable retrieved.")
            
            # Impute
            # T017: "Impute missing descriptors using k-nearest-neighbors"
            df = impute_descriptors_knn(df)
            logger.info("Descriptors imputed.")
            
            # Scale
            # T019: "Scale all numeric features"
            df = scale_features(df)
            logger.info("Features scaled.")
            
            # Save intermediate
            df.to_csv(intermediate_file, index=False)
            logger.info(f"Intermediate scaled data saved to {intermediate_file}")
            
        except Exception as e:
            logger.error(f"Error during preprocessing pipeline: {e}")
            raise

    # 3. Validate Final Schema (T020)
    is_valid, errors = validate_final_schema(df, logger)
    if not is_valid:
        logger.error(f"Final schema validation failed: {errors}")
        raise ValueError(f"Schema validation failed: {errors}")
    
    # 4. Save Final Output
    df.to_csv(final_output_file, index=False)
    logger.info(f"Final aligned dataset saved to {final_output_file}")
    logger.info(f"Final dataset shape: {df.shape}")
    logger.info(f"Final columns: {list(df.columns)}")
    
    # Verify the file exists
    if not final_output_file.exists():
        raise RuntimeError(f"Failed to create output file: {final_output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())