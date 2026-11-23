import os
import sys
import logging
import gc
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, Descriptors3D
from datasets import load_dataset

# Import project utilities
from utils.config import get_config_summary, load_hyperparameters
from utils.logging_config import get_logger, setup_logging
from utils.validators import enforce_2d_only_imports, validate_descriptor_computation_context

# Configure logging
logger = get_logger(__name__)

# Constants
DESCRIPTOR_EXCLUSIONS = [
    'TPSA', 'TPSA_E', 'TPSA_E2', 'TPSA_E3', 'TPSA_E4', 'TPSA_E5',
    'TPSA_E6', 'TPSA_E7', 'TPSA_E8', 'TPSA_E9', 'TPSA_E10'
]

# Hardcoded seed for reproducibility (T004)
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def get_2d_descriptor_names() -> List[str]:
    """
    Returns a list of 2D descriptor names from RDKit, excluding TPSA and 3D descriptors.
    """
    # Get all available descriptors
    all_descs = []
    for name in dir(Descriptors):
        if not name.startswith('_') and callable(getattr(Descriptors, name)):
            all_descs.append(name)
    
    # Filter out excluded names and 3D descriptors
    # Note: Descriptors3D are in a separate module, but we ensure we only use Descriptors
    filtered_descs = [
        name for name in all_descs 
        if name not in DESCRIPTOR_EXCLUSIONS 
        and '3D' not in name
    ]
    
    logger.info(f"Total 2D descriptors available: {len(all_descs)}")
    logger.info(f"Descriptors after filtering: {len(filtered_descs)}")
    logger.info(f"Excluded: {DESCRIPTOR_EXCLUSIONS}")
    
    return filtered_descs

def compute_descriptor_for_molecule(mol: Chem.Mol, descriptor_names: List[str]) -> Dict[str, float]:
    """
    Computes all 2D descriptors for a single molecule.
    Returns a dictionary of descriptor_name: value.
    """
    results = {}
    for name in descriptor_names:
        try:
            func = getattr(Descriptors, name)
            value = func(mol)
            # Handle NaN/Inf
            if pd.isna(value) or np.isinf(value):
                results[name] = np.nan
            else:
                results[name] = float(value)
        except Exception as e:
            # Log error but continue
            logger.warning(f"Error computing {name}: {e}")
            results[name] = np.nan
    return results

def load_batch_iterative(dataset_name: str = 'jablonkagroup/qm9', config_name: str = 'raw_data') -> Any:
    """
    Loads QM9 dataset in streaming mode to handle large datasets without OOM.
    Returns an iterable dataset object.
    """
    logger.info(f"Loading dataset: {dataset_name}/{config_name} in streaming mode")
    try:
        dataset_dict = load_dataset(dataset_name, config_name, streaming=True)
        # Return the first split (usually 'train' or 'raw')
        # We iterate over all splits to get total data
        return dataset_dict
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def compute_descriptors_batch(dataset_iter: Any, descriptor_names: List[str], 
                              output_path: Path, chunk_size: int = 1000) -> None:
    """
    Iterates through the dataset, computes descriptors, and saves in chunks to parquet.
    """
    all_data = []
    total_count = 0
    chunk_count = 0
    
    # We need to iterate over all splits
    for split_name, split_data in dataset_iter.items():
        logger.info(f"Processing split: {split_name}")
        
        # Convert to list if not already, but we want to stream
        # Since we are streaming, we iterate directly
        for idx, record in enumerate(split_data):
            smiles = record.get('SMILES')
            if not smiles:
                continue
            
            # Get target (dipole_moment or similar - QM9 has 'dipole_moment')
            # The schema says: polarizability is the target for polarity prediction
            target = record.get('polarizability')
            if target is None:
                target = record.get('dipole_moment') # Fallback
            
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue
                
                # Compute descriptors
                desc_values = compute_descriptor_for_molecule(mol, descriptor_names)
                
                # Add smiles and target
                row = {'smiles': smiles, 'target': float(target) if target else np.nan}
                row.update(desc_values)
                all_data.append(row)
                total_count += 1
                
                # Save chunk if needed
                if len(all_data) >= chunk_size:
                    chunk_df = pd.DataFrame(all_data)
                    chunk_file = output_path.parent / f"{output_path.stem}_chunk_{chunk_count}.parquet"
                    chunk_df.to_parquet(chunk_file, index=False)
                    logger.info(f"Saved chunk {chunk_count} with {len(all_data)} rows to {chunk_file}")
                    all_data = []
                    chunk_count += 1
                    gc.collect()
                    
            except Exception as e:
                logger.warning(f"Error processing record {idx}: {e}")
                continue

    # Save remaining
    if all_data:
        chunk_df = pd.DataFrame(all_data)
        chunk_file = output_path.parent / f"{output_path.stem}_chunk_{chunk_count}.parquet"
        chunk_df.to_parquet(chunk_file, index=False)
        logger.info(f"Saved final chunk {chunk_count} with {len(all_data)} rows")
        total_count += len(all_data)
    
    logger.info(f"Total records processed: {total_count}")

def handle_missing_values(df: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Handles missing values:
    - If >5% missing in a column, drop the record (row)
    - Otherwise, impute with column median
    """
    logger.info(f"Handling missing values (threshold: {threshold*100}%)")
    initial_rows = len(df)
    
    # Calculate missing percentage per column
    missing_pct = df.isna().sum() / len(df)
    
    # Identify columns to drop (rows with >5% missing in ANY column)
    # Actually, the task says: "If >5% missing values in a column, drop the record"
    # This is ambiguous. Usually it means: if a column has >5% missing overall, drop that column.
    # Or: if a row has >5% missing in a specific column?
    # Re-reading T016: "If >5% missing values in a column, drop the record" -> likely means:
    # If a column has >5% missing values overall, drop all rows that have missing in that column?
    # Or drop the column?
    # Let's interpret as: If a column has >5% missing, we drop the rows that have missing in that column.
    # But the task says "drop the record" (row).
    # Let's follow T016 logic: >5% missing in a column -> drop the record (row) that has missing.
    # This is aggressive. Let's assume: if a row has missing in a column where that column has >5% missing overall, drop the row.
    
    cols_to_drop_rows = missing_pct[missing_pct > threshold].index.tolist()
    
    if cols_to_drop_rows:
        logger.warning(f"Columns with >{threshold*100}% missing: {cols_to_drop_rows}")
        # Drop rows where ANY of these columns are missing
        mask = df[cols_to_drop_rows].isna().any(axis=1)
        dropped_rows = mask.sum()
        df = df[~mask]
        logger.info(f"Dropped {dropped_rows} rows due to missing values in high-missing columns")
    
    # Impute remaining NaNs with median
    for col in df.columns:
        if col in ['smiles', 'target']:
            continue
        if df[col].isna().any():
            median_val = df[col].median()
            if pd.isna(median_val):
                # If median is also NaN (all NaN), fill with 0
                df[col] = df[col].fillna(0.0)
            else:
                df[col] = df[col].fillna(median_val)
    
    final_rows = len(df)
    logger.info(f"Rows before: {initial_rows}, after: {final_rows}")
    return df

def compute_correlation_audit(df: pd.DataFrame, descriptor_names: List[str], log_path: Path) -> None:
    """
    Computes Pearson correlation between descriptors and target.
    Logs any descriptors with |r| > 0.85 to logs/correlation_audit.log.
    DOES NOT remove them.
    """
    logger.info("Running correlation audit")
    
    correlations = {}
    for name in descriptor_names:
        if name in df.columns and 'target' in df.columns:
            corr = df[name].corr(df['target'])
            correlations[name] = corr
    
    # Log high correlations
    high_corr = {k: v for k, v in correlations.items() if abs(v) > 0.85}
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write("Correlation Audit Report\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total descriptors: {len(descriptor_names)}\n")
        f.write(f"High correlations (|r| > 0.85): {len(high_corr)}\n\n")
        if high_corr:
            f.write("Highly Correlated Descriptors:\n")
            for name, corr in sorted(high_corr.items(), key=lambda x: abs(x[1]), reverse=True):
                f.write(f"  {name}: {corr:.4f}\n")
        else:
            f.write("No descriptors with |r| > 0.85 found.\n")
    
    logger.info(f"Correlation audit saved to {log_path}")
    if high_corr:
        logger.warning(f"Found {len(high_corr)} descriptors with |r| > 0.85. They are NOT removed.")

def save_descriptors_batch(chunks_dir: Path, output_path: Path) -> pd.DataFrame:
    """
    Merges all chunk parquet files into a single output file.
    """
    chunk_files = sorted(chunks_dir.glob(f"{output_path.stem}_chunk_*.parquet"))
    if not chunk_files:
        logger.error("No chunk files found to merge")
        return pd.DataFrame()
    
    logger.info(f"Merging {len(chunk_files)} chunk files")
    dfs = []
    for cf in chunk_files:
        try:
            df = pd.read_parquet(cf)
            dfs.append(df)
            os.remove(cf) # Clean up
        except Exception as e:
            logger.error(f"Error reading {cf}: {e}")
    
    if not dfs:
        return pd.DataFrame()
    
    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_parquet(output_path, index=False)
    logger.info(f"Saved merged descriptors to {output_path} with {len(final_df)} rows")
    return final_df

def preprocess_2d(input_dataset: Optional[str] = None, output_path: Optional[str] = None) -> None:
    """
    Main function to preprocess 2D descriptors.
    """
    # Default paths
    if output_path is None:
        output_path = Path("data/processed/descriptors.parquet")
    else:
        output_path = Path(output_path)
    
    # Ensure directories
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get descriptor names
    descriptor_names = get_2d_descriptor_names()
    
    # Load dataset
    dataset_iter = load_batch_iterative()
    
    # Compute descriptors in streaming mode
    chunks_dir = output_path.parent
    compute_descriptors_batch(dataset_iter, descriptor_names, output_path, chunk_size=5000)
    
    # Merge chunks
    df = save_descriptors_batch(chunks_dir, output_path)
    
    if df.empty:
        logger.error("No data processed")
        return
    
    # Handle missing values
    df = handle_missing_values(df)
    
    # Save again after handling missing
    df.to_parquet(output_path, index=False)
    logger.info(f"Final saved to {output_path}")
    
    # Correlation audit
    log_path = Path("logs/correlation_audit.log")
    compute_correlation_audit(df, descriptor_names, log_path)
    
    # Verification
    expected_cols = 2 + len(descriptor_names)
    actual_cols = len(df.columns)
    assert actual_cols == expected_cols, f"Column count mismatch: expected {expected_cols}, got {actual_cols}"
    
    # Check for excluded columns
    for exc in DESCRIPTOR_EXCLUSIONS:
        assert exc not in df.columns, f"Excluded column {exc} found in output"
    
    logger.info("Preprocessing complete. Verification passed.")

def main():
    """
    Entry point for the script.
    """
    setup_logging()
    logger.info("Starting 2D descriptor preprocessing")
    
    try:
        preprocess_2d()
        logger.info("Preprocessing completed successfully")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()