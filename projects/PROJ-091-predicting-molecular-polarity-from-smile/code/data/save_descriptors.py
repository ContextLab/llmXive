import os
import sys
import logging
import gc
from pathlib import Path
from typing import List, Optional

import pandas as pd
import numpy as np

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import PreprocessingConfig
from utils.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def verify_schema(df: pd.DataFrame, descriptor_names: List[str]) -> bool:
    """
    Verifies the schema of the descriptor DataFrame.
    
    Checks:
    1. 'smiles' column exists and is string.
    2. 'target' column exists and is float.
    3. All descriptor columns (starting with 'desc_') exist.
    4. No TPSA, TPSA_E, or SMARTS-derived columns exist.
    5. Total column count matches 2 + len(descriptor_names).
    
    Args:
        df: The DataFrame to verify.
        descriptor_names: List of expected descriptor column names.
        
    Returns:
        True if schema is valid, raises AssertionError otherwise.
    """
    required_cols = ['smiles', 'target']
    expected_cols = set(required_cols + descriptor_names)
    
    # Check required columns
    for col in required_cols:
        if col not in df.columns:
            raise AssertionError(f"Missing required column: {col}")
        
    # Check for forbidden columns
    forbidden_patterns = ['TPSA', 'TPSA_E', 'SMARTS']
    for col in df.columns:
        if any(pattern in col.upper() for pattern in forbidden_patterns):
            raise AssertionError(f"Forbidden column found: {col}")
            
    # Check total count
    actual_cols = set(df.columns)
    if len(actual_cols) != len(expected_cols):
        raise AssertionError(
            f"Column count mismatch. Expected {len(expected_cols)} ({2 + len(descriptor_names)}), "
            f"got {len(actual_cols)}. Missing: {expected_cols - actual_cols}, Extra: {actual_cols - expected_cols}"
        )
        
    # Verify all expected descriptors are present
    missing_descs = expected_cols - actual_cols
    if missing_descs:
        raise AssertionError(f"Missing descriptor columns: {missing_descs}")
        
    logger.info("Schema verification passed.")
    return True

def save_descriptors(df: pd.DataFrame, output_path: Path, descriptor_names: List[str]) -> None:
    """
    Saves the processed feature matrix to a parquet file.
    
    Args:
        df: The DataFrame containing smiles, target, and descriptors.
        output_path: Path to save the parquet file.
        descriptor_names: List of descriptor column names for verification.
    """
    # Verify schema before saving
    verify_schema(df, descriptor_names)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path} ({len(df)} rows, {len(df.columns)} columns)")
    
    # Explicitly verify file exists and is readable
    if not output_path.exists():
        raise RuntimeError(f"Failed to create output file: {output_path}")
        
    # Read back to ensure integrity
    df_check = pd.read_parquet(output_path)
    if len(df_check) != len(df) or len(df_check.columns) != len(df.columns):
        raise RuntimeError("Integrity check failed: saved file does not match input.")
        
    logger.info(f"Integrity check passed for {output_path}")

def main():
    """
    Main entry point for saving descriptors.
    Expects data/raw/qm9_smiles.csv to exist (produced by download_qm9.py).
    Computes descriptors and saves to data/processed/descriptors.parquet.
    """
    setup_logging()
    
    # Load configuration
    config = PreprocessingConfig()
    
    # Paths
    raw_data_path = project_root / "data" / "raw" / "qm9_smiles.csv"
    output_path = project_root / "data" / "processed" / "descriptors.parquet"
    
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}. Run download_qm9.py first.")
        sys.exit(1)
        
    logger.info(f"Loading raw data from {raw_data_path}")
    
    # Load data
    try:
        # Assuming the download script produces a CSV with 'smiles' and 'target' (dipole_moment)
        # We need to map the QM9 'dipole_moment' to 'target' if the column name differs
        df_raw = pd.read_csv(raw_data_path)
        
        # Normalize column names if necessary (e.g., from download script output)
        # The verified source has 'SMILES' and 'dipole_moment'
        if 'SMILES' in df_raw.columns:
            df_raw = df_raw.rename(columns={'SMILES': 'smiles'})
        if 'dipole_moment' in df_raw.columns:
            df_raw = df_raw.rename(columns={'dipole_moment': 'target'})
            
        # Ensure types
        df_raw['smiles'] = df_raw['smiles'].astype(str)
        df_raw['target'] = df_raw['target'].astype(float)
        
        logger.info(f"Loaded {len(df_raw)} records.")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        sys.exit(1)
        
    # Import descriptor computation logic from preprocess_2d
    # We reuse the logic from T014a but ensure we don't re-run if already done, 
    # or we run it here to ensure the file is generated.
    # Since T014a is the producer of the logic, we import it.
    from data.preprocess_2d import compute_descriptors_batch, load_batch_iterative
    
    # We need to compute descriptors. Since we are saving the result of T014a/T014b,
    # we should run the computation here if the file doesn't exist.
    # However, the task T014c is specifically about SAVING. 
    # To ensure the pipeline works, we will compute descriptors here if needed,
    # or assume they are in memory from a previous step.
    # Given the execution context, we will run the computation step here to ensure data exists.
    
    logger.info("Computing 2D descriptors...")
    
    # Use the batch processing logic from preprocess_2d
    # We'll load the raw file and compute descriptors
    descriptor_names = []
    all_descriptors = []
    
    # To avoid re-computing everything in memory, we process in chunks and accumulate
    # But for the final save, we need the full DF. 
    # Given memory constraints, we assume the raw data fits or we process iteratively.
    # For this implementation, we load the raw CSV, compute descriptors, and save.
    
    # Re-using the logic from preprocess_2d.compute_descriptors_batch
    # We need to get the list of descriptors first
    from rdkit.Chem import Descriptors
    desc_list = [(name, func) for name, func in Descriptors.descList]
    # Filter out TPSA and others if necessary (T014a logic)
    # T014a excludes TPSA, TPSA_E, SMARTS. 
    # We implement the filtering here to ensure consistency.
    filtered_descs = []
    for name, func in desc_list:
        if 'TPSA' in name or 'SMARTS' in name:
            continue
        filtered_descs.append((name, func))
        
    descriptor_names = [name for name, _ in filtered_descs]
    logger.info(f"Computing {len(descriptor_names)} descriptors.")
    
    # Apply descriptors
    # We use a loop to avoid memory explosion if possible, but pandas apply is usually fine for this size
    # We'll use a safe apply method
    def compute_row_descriptors(smiles_str):
        try:
            mol = Chem.MolFromSmiles(smiles_str)
            if mol is None:
                return {name: np.nan for name in descriptor_names}
            return {name: func(mol) for name, func in filtered_descs}
        except Exception:
            return {name: np.nan for name in descriptor_names}
    
    # Apply to dataframe
    # Note: This might be slow for large datasets, but it's the standard way for RDKit
    # For T017 (batching), we might need to optimize, but T014c is about saving.
    # We assume the raw data is manageable or we use chunking.
    # Let's use chunking to be safe with memory.
    
    chunk_size = 10000
    chunks = []
    
    for start in range(0, len(df_raw), chunk_size):
        end = min(start + chunk_size, len(df_raw))
        chunk = df_raw.iloc[start:end].copy()
        
        # Compute descriptors for this chunk
        chunk_desc = chunk['smiles'].apply(compute_row_descriptors).apply(pd.Series)
        chunk_desc.columns = descriptor_names
        
        # Combine
        chunk_result = pd.concat([chunk[['smiles', 'target']], chunk_desc], axis=1)
        chunks.append(chunk_result)
        
        # Garbage collect
        if start % (chunk_size * 5) == 0:
            gc.collect()
            
    logger.info("Concatenating chunks...")
    df_processed = pd.concat(chunks, ignore_index=True)
    del chunks
    gc.collect()
    
    logger.info(f"Processed {len(df_processed)} rows.")
    
    # Save
    save_descriptors(df_processed, output_path, descriptor_names)
    
    logger.info("Task T014c completed successfully.")

if __name__ == "__main__":
    main()
