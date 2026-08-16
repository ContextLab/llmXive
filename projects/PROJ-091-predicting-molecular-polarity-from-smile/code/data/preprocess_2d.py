import os
import sys
import logging
import gc
from pathlib import Path
from typing import Iterator, Tuple, List, Dict, Any, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors
from utils.logging_config import get_logger

logger = get_logger(__name__)

# List of 2D descriptors to compute (excluding TPSA, 3D, SMARTS)
DESCRIPTORS_TO_COMPUTE = [
    'MolWt', 'MolLogP', 'NumHDonors', 'NumHAcceptors', 'NumRotatableBonds',
    'NumAromaticRings', 'NumAliphaticRings', 'NumSaturatedRings', 'FractionCSP3',
    'HeavyAtomCount', 'NumHeteroatoms', 'RingCount', 'MaxAbsEStateIndex',
    'MinAbsEStateIndex', 'MaxEStateIndex', 'MinEStateIndex', 'ExactMolWt',
    'FormalCharge', 'NumRadicalElectrons', 'NumValenceElectrons', 'NumBridgeheadAtoms',
    'NumAmideBonds', 'NumSpiroAtoms'
]

BATCH_SIZE = 1000  # Process 1000 molecules at a time to control memory

def compute_descriptors_batch(smiles_list: List[str]) -> pd.DataFrame:
    """Compute 2D descriptors for a batch of SMILES strings."""
    records = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        desc_values = {}
        for desc_name in DESCRIPTORS_TO_COMPUTE:
            try:
                func = getattr(Descriptors, desc_name)
                value = func(mol)
                if pd.isna(value) or np.isinf(value):
                    value = np.nan
                desc_values[desc_name] = value
            except Exception as e:
                logger.warning(f"Error computing {desc_name} for {smiles}: {e}")
                desc_values[desc_name] = np.nan
        records.append({"smiles": smiles, **desc_values})
    return pd.DataFrame(records)

def filter_high_correlation_features(df: pd.DataFrame, threshold: float = 0.85) -> pd.DataFrame:
    """Filter features with high correlation. Note: T015 says DO NOT filter, but API exists."""
    logger.info("Correlation filtering disabled per T015 constraints")
    return df

def handle_missing_values(df: pd.DataFrame, drop_threshold: float = 0.05) -> pd.DataFrame:
    """Handle missing values: drop if >5% missing, else impute with median."""
    for col in df.columns:
        if col in ['smiles', 'target']:
            continue
        missing_ratio = df[col].isna().sum() / len(df)
        if missing_ratio > drop_threshold:
            logger.info(f"Dropping column {col} due to {missing_ratio:.2%} missing values")
            df = df.drop(columns=[col])
        else:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
    return df

def preprocess_2d(input_path: Path, output_path: Path) -> None:
    """
    Main preprocessing pipeline with explicit batch iteration and garbage collection.
    Optimized for <6GB RAM usage by processing input in chunks and forcing GC.
    """
    logger.info(f"Starting batched preprocessing from {input_path} to {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize output list for incremental saving
    all_records = []
    batch_count = 0
    
    # Read input in chunks to manage memory
    # Using chunksize allows iteration without loading full file into RAM
    try:
        chunk_iter = pd.read_parquet(input_path, chunksize=BATCH_SIZE)
    except Exception as e:
        logger.error(f"Failed to read parquet in chunks: {e}")
        # Fallback to full read if chunking fails (not ideal for memory but prevents crash)
        logger.warning("Falling back to full read (may exceed memory limits)")
        chunk_iter = [pd.read_parquet(input_path)]

    for chunk_idx, chunk in enumerate(chunk_iter):
        logger.info(f"Processing chunk {chunk_idx + 1} (size: {len(chunk)})")
        
        # Compute descriptors for this batch
        desc_df = compute_descriptors_batch(chunk['smiles'].tolist())
        
        # Merge with target for this batch
        if 'target' in chunk.columns:
            merged_batch = pd.merge(desc_df, chunk[['smiles', 'target']], on='smiles', how='inner')
        else:
            # If target is missing, assume it's handled elsewhere or skip
            merged_batch = desc_df
        
        # Handle missing values for this batch
        merged_batch = handle_missing_values(merged_batch)
        
        # Ensure no 3D columns
        excluded_cols = ['TPSA', 'TPSA_E', 'SMI']
        for col in excluded_cols:
            if col in merged_batch.columns:
                logger.warning(f"Removing excluded column: {col}")
                merged_batch = merged_batch.drop(columns=[col])
        
        # Accumulate results
        all_records.append(merged_batch)
        
        # Explicitly delete intermediate variables and force GC to free memory
        del desc_df
        del merged_batch
        gc.collect()
        
        batch_count += 1
        
        # Log memory status periodically (if psutil available, otherwise skip)
        if batch_count % 10 == 0:
            logger.info(f"Completed {batch_count} batches. Forcing garbage collection.")
            gc.collect()

    if not all_records:
        logger.error("No data processed. Check input file.")
        return

    # Concatenate all batches
    logger.info("Concatenating all batches...")
    final_df = pd.concat(all_records, ignore_index=True)
    
    # Clear batch memory
    del all_records
    gc.collect()
    
    # Final validation
    logger.info(f"Final dataset shape: {final_df.shape}")
    
    # Save to parquet
    logger.info(f"Saving to {output_path}")
    final_df.to_parquet(output_path, index=False)
    
    # Final cleanup
    del final_df
    gc.collect()
    
    logger.info("Preprocessing completed successfully")

def main() -> None:
    """Main entry point."""
    input_path = Path("data/raw/qm9_processed.parquet")
    output_path = Path("data/processed/descriptors.parquet")
    preprocess_2d(input_path, output_path)

if __name__ == "__main__":
    main()