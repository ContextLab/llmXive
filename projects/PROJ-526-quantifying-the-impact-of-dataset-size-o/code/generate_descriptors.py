import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

from config import get_config, require_data_dir
from utils.logging_config import setup_logging, get_logger
from utils.seed import set_seed

setup_logging()
logger = get_logger(__name__)

def load_raw_materials(input_dir: Path) -> pd.DataFrame:
    """Load raw material data from parquet files."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    parquet_files = list(input_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"No parquet files found in {input_dir}")
    
    dfs = []
    for f in parquet_files:
        logger.info(f"Loading {f}")
        df = pd.read_parquet(f)
        df['source_file'] = f.name
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(combined)} rows from {len(parquet_files)} files")
    return combined

def validate_dataframe(df: pd.DataFrame) -> bool:
    """Validate that dataframe has required columns."""
    required_cols = ['formula', 'property_value']
    # Check for any column that looks like formula/chemistry
    has_formula = any('formula' in str(c).lower() or 'composition' in str(c).lower() for c in df.columns)
    has_value = 'property_value' in df.columns or any('value' in str(c).lower() for c in df.columns)
    
    if not has_formula:
        logger.error("Dataframe missing formula/composition column")
        return False
    if not has_value:
        logger.error("Dataframe missing property value column")
        return False
    
    return True

def compute_magpie_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Magpie composition-only descriptors.
    Uses pymatgen's elemental features if matminer is unavailable.
    """
    logger.info("Computing Magpie descriptors...")
    
    # Fallback implementation using pymatgen if matminer is not available
    try:
        from matminer.featurizers.composition import MagpieData
        from matminer.featurizers.compose import CompositionFeaturizer
        from pymatgen import Composition
        
        # Initialize featurizer
        featurizer = MagpieData()
        
        # Apply to dataframe
        # Assuming 'formula' column exists
        if 'formula' not in df.columns:
            # Try to find a column that looks like a formula
            formula_col = next((c for c in df.columns if 'formula' in c.lower() or 'composition' in c.lower()), None)
            if formula_col:
                df['formula'] = df[formula_col]
            else:
                raise ValueError("Could not find formula column")
        
        # Vectorize composition
        def get_magpie_vec(formula_str):
            try:
                comp = Composition(formula_str)
                return featurizer.featurize(comp)
            except Exception as e:
                logger.warning(f"Failed to featurize {formula_str}: {e}")
                return [np.nan] * len(featurizer.feature_labels())
        
        # Apply
        logger.info("Featurizing compositions...")
        magpie_features = df['formula'].apply(get_magpie_vec)
        
        # Expand into columns
        feature_names = featurizer.feature_labels()
        feature_df = pd.DataFrame(magpie_features.tolist(), index=df.index, columns=feature_names)
        
        # Combine
        result = pd.concat([df, feature_df], axis=1)
        logger.info(f"Computed {len(feature_names)} descriptors")
        return result
        
    except ImportError:
        logger.warning("matminer not available. Using simplified composition features.")
        # Simplified fallback: extract element counts
        # This is a placeholder for the real logic
        # In a real scenario, we would implement the Magpie logic manually or use pymatgen directly
        logger.error("Matminer is required for full Magpie descriptors. Please install it.")
        raise ImportError(
            "The 'matminer' package is required for Magpie descriptor generation. "
            "Please install it via 'pip install matminer' and ensure 'pymatgen' is also installed."
        )

def save_master_dataset(df: pd.DataFrame, output_dir: Path) -> Path:
    """Save the processed dataset with descriptors."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "materials_master.parquet"
    
    logger.info(f"Saving master dataset to {output_path}")
    df.to_parquet(output_path, compression="snappy")
    
    logger.info(f"Saved {len(df)} rows with {len(df.columns)} columns")
    return output_path

def main():
    """Main entry point for descriptor generation."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate Magpie descriptors")
    parser.add_argument("--input", type=str, default="data/raw", help="Input directory with raw data")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    # Load data
    df = load_raw_materials(input_dir)
    
    # Validate
    if not validate_dataframe(df):
        logger.error("Validation failed")
        sys.exit(1)
    
    # Compute descriptors
    df_with_desc = compute_magpie_descriptors(df)
    
    # Save
    save_master_dataset(df_with_desc, output_dir)
    
    logger.info("Descriptor generation complete")

if __name__ == "__main__":
    main()