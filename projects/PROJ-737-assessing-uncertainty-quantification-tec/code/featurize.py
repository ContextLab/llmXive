"""
Featurization module for materials property prediction.

Converts raw compositions/structures to feature vectors using matminer (fallback to pymatgen).
Implements memory-aware loading, stratified splitting, and sample capping.
"""
import os
import gc
import logging
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Attempt matminer import, fallback to pymatgen
try:
    from matminer.featurizers.composition import ElementProperty
    from matminer.featurizers.structure import StructureFeaturizer
    from matminer.utils.io import load_structure
    HAS_MATMINER = True
except ImportError:
    HAS_MATMINER = False
    try:
        from pymatgen.analysis.structure_analyzer import oxidation_state
        from pymatgen.core import Composition, Structure
        from pymatgen.transformations.standard_transformations import OrderDisorderTransformation
        HAS_PYMATGEN = True
    except ImportError:
        HAS_PYMATGEN = False
        raise ImportError("Neither matminer nor pymatgen is installed. Please install one of them.")

logger = logging.getLogger(__name__)

# Constants
RANDOM_SEED = 42
MAX_MEMORY_GB = 1.8
DEFAULT_CAP = 5000  # Default cap if "deferred" is not resolved, adjusted dynamically if memory exceeds
OUTPUT_DIR = Path("data/processed")
RAW_DATA_DIR = Path("data/raw")

def get_memory_usage_gb() -> float:
    """Estimate current memory usage in GB."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed. Memory checks disabled. Assuming safe.")
        return 0.0

def load_raw_data(dataset_name: str) -> pd.DataFrame:
    """Load raw dataset from data/raw/ directory."""
    file_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    
    logger.info(f"Loading raw data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Ensure expected columns exist (adapt based on download.py output)
    # Expected: composition (string), property_value (float), structure (optional string/json)
    required_cols = ['composition', 'property_value']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {dataset_name}: {missing}")
    
    return df

def featurize_composition(composition_str: str) -> np.ndarray:
    """Convert composition string to feature vector."""
    if HAS_MATMINER:
        try:
            feat = ElementProperty.from_preset("magpie")
            # matminer expects a Composition object or string
            return feat.featurize(composition_str)
        except Exception as e:
            logger.warning(f"Matminer featurization failed for {composition_str}: {e}")
            raise
    elif HAS_PYMATGEN:
        try:
            comp = Composition(composition_str)
            # Simple fallback: element count vector (not ideal, but works)
            # In a real scenario, we'd need a more robust fallback featurizer
            # For now, we'll raise if matminer fails and pymatgen can't do it well
            raise NotImplementedError("Pymatgen fallback for complex featurization not fully implemented in this context.")
        except Exception as e:
            logger.error(f"Pymatgen fallback failed: {e}")
            raise
    else:
        raise ImportError("No featurization library available.")

def featurize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply featurization to the entire dataframe."""
    logger.info("Starting featurization...")
    feature_list = []
    
    for idx, row in df.iterrows():
        try:
            features = featurize_composition(row['composition'])
            feature_list.append(features)
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to featurization error: {e}")
            continue
        
        # Memory check loop
        mem_gb = get_memory_usage_gb()
        if mem_gb > MAX_MEMORY_GB:
            logger.warning(f"Memory usage ({mem_gb:.2f} GB) exceeded threshold. Stopping featurization early.")
            break

    if not feature_list:
        raise ValueError("No features were generated. Check input data and featurizer.")

    # Create feature dataframe
    feat_df = pd.DataFrame(feature_list)
    feat_df.columns = [f"f_{i}" for i in range(feat_df.shape[1])]
    
    # Attach original data (excluding composition if not needed, but keeping for reference)
    result_df = pd.concat([df.reset_index(drop=True), feat_df.reset_index(drop=True)], axis=1)
    
    logger.info(f"Featurization complete. Shape: {result_df.shape}")
    return result_df

def stratified_split(
    df: pd.DataFrame, 
    target_col: str, 
    test_size: float = 0.2, 
    val_size: float = 0.1,
    n_bins: int = 10
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train/val/test split based on property range.
    Uses quantile-based bins.
    """
    np.random.seed(RANDOM_SEED)
    
    # Create quantile bins
    df['bin'] = pd.qcut(df[target_col], q=n_bins, labels=False, duplicates='drop')
    
    # Shuffle
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    
    # Split by bins
    train_df = pd.DataFrame()
    val_df = pd.DataFrame()
    test_df = pd.DataFrame()
    
    for bin_val in df['bin'].unique():
        subset = df[df['bin'] == bin_val]
        n = len(subset)
        
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        
        # Ensure at least 1 if n is large enough, else 0
        if n > 1:
            n_test = max(1, n_test)
            n_val = max(1, n_val) if n - n_test > 0 else 0
        
        indices = np.arange(n)
        np.random.shuffle(indices)
        
        test_indices = indices[:n_test]
        val_indices = indices[n_test:n_test+n_val]
        train_indices = indices[n_test+n_val:]
        
        if len(test_indices) > 0:
            test_df = pd.concat([test_df, subset.iloc[test_indices]], ignore_index=True)
        if len(val_indices) > 0:
            val_df = pd.concat([val_df, subset.iloc[val_indices]], ignore_index=True)
        if len(train_indices) > 0:
            train_df = pd.concat([train_df, subset.iloc[train_indices]], ignore_index=True)
    
    # Drop the temporary bin column
    for d in [train_df, val_df, test_df]:
        if 'bin' in d.columns:
            d.drop(columns=['bin'], inplace=True)
    
    logger.info(f"Split sizes - Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")
    return train_df, val_df, test_df

def process_dataset(dataset_name: str, cap: Optional[int] = None) -> Dict[str, pd.DataFrame]:
    """
    Main processing pipeline for a dataset:
    1. Load raw data
    2. Apply cap
    3. Featurize
    4. Memory check (downsample if needed)
    5. Stratified split
    6. Save to data/processed/
    """
    if cap is None:
        cap = DEFAULT_CAP
    
    logger.info(f"Processing dataset: {dataset_name} with cap {cap}")
    
    # 1. Load
    df = load_raw_data(dataset_name)
    
    # 2. Cap
    if len(df) > cap:
        logger.info(f"Dataset size ({len(df)}) exceeds cap ({cap}). Downsampling.")
        df = df.sample(n=cap, random_state=RANDOM_SEED).reset_index(drop=True)
    
    # 3. Featurize
    try:
        df_feat = featurize_dataframe(df)
    except Exception as e:
        logger.error(f"Featurization failed for {dataset_name}: {e}")
        raise
    
    # 4. Memory check & downsample if necessary
    mem_gb = get_memory_usage_gb()
    if mem_gb > MAX_MEMORY_GB:
        logger.warning(f"Memory usage ({mem_gb:.2f} GB) exceeded threshold after featurization. Downsampling further.")
        current_size = len(df_feat)
        target_size = int(current_size * 0.5) # Reduce by half
        if target_size < 100:
            target_size = 100 # Minimum threshold
        
        df_feat = df_feat.sample(n=target_size, random_state=RANDOM_SEED).reset_index(drop=True)
        logger.info(f"Downsampled to {len(df_feat)} samples.")
    
    # 5. Split
    target_col = 'property_value'
    train_df, val_df, test_df = stratified_split(df_feat, target_col)
    
    # 6. Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_df.to_csv(OUTPUT_DIR / f"{dataset_name}_train.csv", index=False)
    val_df.to_csv(OUTPUT_DIR / f"{dataset_name}_val.csv", index=False)
    test_df.to_csv(OUTPUT_DIR / f"{dataset_name}_test.csv", index=False)
    
    logger.info(f"Saved processed splits for {dataset_name} to {OUTPUT_DIR}")
    
    return {
        'train': train_df,
        'val': val_df,
        'test': test_df
    }

def main():
    """Entry point for featurization script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Datasets to process (matching download.py)
    datasets = [
        "oqmd_band_gap",
        "oqmd_formation_energy",
        "aflow_thermal_conductivity"
    ]
    
    # Cap can be passed via env or argument, defaulting to logic in function
    # For now, using DEFAULT_CAP logic which includes dynamic adjustment
    cap = int(os.getenv("FEATURIZE_CAP", DEFAULT_CAP))
    
    results = {}
    for ds in datasets:
        try:
            logger.info(f"--- Processing {ds} ---")
            results[ds] = process_dataset(ds, cap)
            gc.collect() # Force garbage collection between datasets
        except Exception as e:
            logger.error(f"Failed to process {ds}: {e}")
            traceback.print_exc()
            # Continue to next dataset to ensure partial progress
            continue
    
    logger.info("Featurization pipeline complete.")
    return results

if __name__ == "__main__":
    main()
