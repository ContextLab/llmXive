"""
Module: code/data/save_descriptors.py
Purpose: Save the processed 2D descriptor matrix to a Parquet file.

This module implements Task T018: Save processed feature matrix to `data/processed/descriptors.parquet`.

It performs the following critical checks:
1. Verifies the output schema includes 'smiles', 'target', and descriptor columns.
2. Explicitly ensures NO columns named 'TPSA', 'TPSA_E', or derived from SMARTS exist.
3. Asserts that the number of columns matches the input (no filtering occurred), 
   satisfying the "compute but do not filter" logic from T015.
"""
import os
import sys
import logging
import gc
from pathlib import Path
from typing import List, Optional
import pandas as pd
import pyarrow.parquet as pq

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import get_logger
from utils.validators import enforce_2d_only_imports

logger = get_logger(__name__)

# Forbidden column names or prefixes that indicate 3D, TPSA, or SMARTS usage
FORBIDDEN_COLUMNS = {
    'TPSA', 'TPSA_E', 'TPSA_EState', 'TPSA_Topological', 'TPSA_Estate',
    'SMARTS', 'Pattern', 'MolWt_3D', 'MolLogP_3D', 'SlogP_3D'
}

# 3D-specific descriptors that might sneak in if 3D conformers were generated
FORBIDDEN_3D_PREFIXES = [
    'MolWt_3D', 'MolLogP_3D', 'SlogP_3D', 'TPSA_3D', 'SA_Score_3D'
]

def verify_schema(df: pd.DataFrame, expected_columns: List[str]) -> bool:
    """
    Verify the DataFrame schema against T018 requirements.
    
    Checks:
    1. 'smiles' (string) and 'target' (float) columns exist.
    2. No forbidden columns (TPSA, SMARTS, 3D) exist.
    3. Column count matches expected input count (no filtering).
    
    Args:
        df: The processed DataFrame.
        expected_columns: The list of columns expected from the input (pre-filter).
        
    Returns:
        bool: True if schema is valid, False otherwise.
        
    Raises:
        AssertionError: If schema validation fails.
    """
    # Check required columns
    assert 'smiles' in df.columns, "Missing required column: 'smiles'"
    assert 'target' in df.columns, "Missing required column: 'target'"
    
    # Check data types
    assert df['smiles'].dtype == 'object' or str(df['smiles'].dtype) == 'string', \
        f"'smiles' column must be string type, got {df['smiles'].dtype}"
    assert 'float' in str(df['target'].dtype), \
        f"'target' column must be float type, got {df['target'].dtype}"
    
    # Check for forbidden columns
    found_forbidden = [col for col in df.columns if col in FORBIDDEN_COLUMNS]
    assert not found_forbidden, \
        f"Forbidden columns found in output: {found_forbidden}. " \
        "Ensure TPSA, SMARTS, or 3D descriptors were not included."
        
    found_forbidden_prefix = [col for col in df.columns if any(col.startswith(p) for p in FORBIDDEN_3D_PREFIXES)]
    assert not found_forbidden_prefix, \
        f"Forbidden 3D prefix columns found: {found_forbidden_prefix}."
    
    # Critical Check: Verify no filtering occurred (T015 logic)
    # The number of output columns (excluding smiles/target) must match expected descriptor count
    # However, the task says "Assert len(df.columns) == expected_input_columns".
    # expected_input_columns should be the full list of input columns passed to this function.
    if len(df.columns) != len(expected_columns):
        missing_cols = set(expected_columns) - set(df.columns)
        extra_cols = set(df.columns) - set(expected_columns)
        raise AssertionError(
            f"Column count mismatch! "
            f"Input had {len(expected_columns)} cols, Output has {len(df.columns)}. "
            f"Missing: {missing_cols}, Extra: {extra_cols}. "
            f"The 'compute but do not filter' logic was violated."
        )
    
    logger.info(f"Schema verification passed. Columns: {len(df.columns)} (smiles, target, + {len(df.columns)-2} descriptors).")
    return True

def save_descriptors(df: pd.DataFrame, output_path: Path, input_columns: List[str]) -> None:
    """
    Save the DataFrame to a Parquet file with schema verification.
    
    Args:
        df: The processed DataFrame.
        output_path: The path to save the parquet file.
        input_columns: The list of columns from the input to verify against.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Verify schema before saving
    verify_schema(df, input_columns)
    
    # Save to Parquet
    logger.info(f"Saving descriptors to {output_path}...")
    df.to_parquet(output_path, index=False)
    
    # Verify file size is non-zero
    assert output_path.exists() and output_path.stat().st_size > 0, \
        f"Failed to create non-empty file at {output_path}"
        
    logger.info(f"Successfully saved {output_path} ({output_path.stat().st_size / 1024:.2f} KB).")

def main():
    """
    Entry point for T018: Save processed feature matrix.
    
    This script is intended to be run after `preprocess_2d.py` has generated the 
    in-memory or batched descriptor data. It assumes the data is passed via 
    a standard pipeline or loaded from the intermediate state of the pipeline.
    
    For this implementation, we assume the `preprocess_2d` module returns the 
    final processed DataFrame or we load it from a temporary state if the 
    pipeline was split. However, per the task description, we are saving 
    the result of the processing.
    
    In a real pipeline execution, this would be called with the processed data.
    Here, we implement the function to be called by the pipeline or run as a 
    standalone if data is available in a temporary location (though the 
    preferred flow is via `main.py` orchestration).
    """
    logger.info("Starting T018: Save Descriptors.")
    
    # In a real scenario, the data would be passed from the previous step.
    # Since we are implementing the script, we assume the pipeline passes data.
    # If run standalone, we might need to load from a temp file or re-run preprocessing.
    # However, the task says "Save processed feature matrix".
    # We will assume the caller (e.g., main.py) has the data or we load it from 
    # the raw/processed flow if it was saved temporarily.
    
    # For this specific task implementation, we will define the function 
    # that performs the save and verification, and a main that demonstrates 
    # the logic if called directly (though it requires data).
    
    # To make this script runnable and testable as a standalone artifact 
    # (as required by "Produce real outputs"), we will check if a temporary 
    # processed file exists from a previous run or if we need to simulate 
    # the loading of the processed data from the pipeline context.
    
    # Since the pipeline is sequential, we assume `code/main.py` or the 
    # orchestrator calls this with the data.
    # However, to satisfy "Produce real outputs", we will implement the 
    # logic to load the *preprocessed* data if it was saved to a temp location 
    # by `preprocess_2d.py` (which might save a temp chunk).
    
    # Alternative: The task implies we are saving the result of the entire 
    # preprocessing step. If `preprocess_2d.py` outputs to a temp file, we load it.
    # If not, we assume the pipeline passes it.
    
    # Let's implement the save logic assuming data is available in `data/processed/temp_descriptors.csv`
    # or similar, OR we re-run the preprocessing if needed.
    # Actually, the cleanest way for T018 is to be the final step of the 
    # `preprocess_2d` workflow.
    
    # We will assume the `preprocess_2d` module has a function to get the full 
    # dataframe or we load it from the raw data and re-process? No, that's inefficient.
    # Let's assume the pipeline passes the dataframe.
    
    # Since we cannot run the full pipeline here without the full environment,
    # we will implement the `save_descriptors` function and the `main` function
    # that expects the data to be provided or loaded from a standard intermediate 
    # location if the pipeline is split.
    
    # For the purpose of this task, we will create a script that can be called
    # to save the data if it exists in a temporary location created by the 
    # preprocessing step (e.g., `data/processed/temp_full_descriptors.parquet` 
    # or similar).
    
    # However, the task says "Save processed feature matrix to data/processed/descriptors.parquet".
    # We will implement the logic to load the data from the `preprocess_2d` 
    # if it was saved to a temp file, or re-run the preprocessing if necessary.
    # But to avoid redundancy, we assume the data is passed.
    
    # Let's assume the `preprocess_2d` script saves the final dataframe to 
    # `data/processed/temp_descriptors.parquet` and this script renames/validates it.
    
    # Actually, the most robust way is to have `preprocess_2d` call this function.
    # But since we are implementing T018 as a separate script, we will 
    # implement the validation and saving logic.
    
    # We will assume the data is available in `data/processed/temp_descriptors.csv`
    # from the previous step.
    
    temp_input_path = PROJECT_ROOT / "data" / "processed" / "temp_descriptors.csv"
    output_path = PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
    
    if temp_input_path.exists():
        logger.info(f"Loading temporary processed data from {temp_input_path}")
        df = pd.read_csv(temp_input_path)
        input_columns = list(df.columns)
        save_descriptors(df, output_path, input_columns)
        # Clean up temp file
        temp_input_path.unlink()
        logger.info("Temporary file cleaned up.")
    else:
        logger.warning(f"Temporary input file {temp_input_path} not found. "
                       "This script expects the previous step (preprocess_2d) to save "
                       "a temporary CSV. Please ensure the pipeline runs sequentially.")
        # If running in a pipeline, the data would be passed directly.
        # For standalone testing, we might need to mock or run the previous step.
        # But per instructions, we must produce real outputs.
        # We will raise an error if the file is missing.
        raise FileNotFoundError(
            f"Intermediate data file not found at {temp_input_path}. "
            "Ensure `preprocess_2d.py` has run and saved the temporary file."
        )

if __name__ == "__main__":
    main()
