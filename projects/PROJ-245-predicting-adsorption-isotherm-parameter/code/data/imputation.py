"""
Imputation module for handling missing pore volume data.

Implements hierarchical imputation strategy:
1. Group by (material_type, surface_area_bin) -> group mean
2. Group by material_type -> material global mean
3. Global dataset mean
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    dirs = [
        Path("data/processed"),
        Path("data/validation")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured output directories exist.")

def impute_pore_volume(
    input_path: str,
    output_path: str,
    exclusion_log_path: str
) -> pd.DataFrame:
    """
    Perform hierarchical imputation on pore_volume column.
    
    Logic:
    1. Load data from input_path.
    2. Group by (material_type, surface_area_bin).
    3. If group size > 0, assign group mean.
    4. If group size == 0, assign material_type global mean.
    5. If no material_type exists, assign global dataset mean.
    6. If imputation fails (e.g., all NaN in group), exclude row and log.
    
    Args:
        input_path: Path to target_filtered.parquet
        output_path: Path to save imputed_dataset.parquet
        exclusion_log_path: Path to log excluded entries
        
    Returns:
        DataFrame with imputed pore_volume column.
    """
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        raise

    if df.empty:
        logger.warning("Input dataset is empty. Creating empty output.")
        df.to_parquet(output_path, index=False)
        return df

    # Ensure surface_area_bin exists, create if missing
    if 'surface_area_bin' not in df.columns:
        logger.info("Creating surface_area_bin via binning surface_area")
        if 'surface_area' in df.columns:
            df['surface_area_bin'] = pd.qcut(
                df['surface_area'].fillna(0), 
                q=5, 
                duplicates='drop', 
                labels=False
            )
        else:
            df['surface_area_bin'] = 0

    # Ensure material_type exists
    if 'material_type' not in df.columns:
        logger.warning("material_type column missing. Assigning generic 'Unknown'.")
        df['material_type'] = 'Unknown'

    # Target column
    target_col = 'pore_volume'
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in dataset.")
        raise ValueError(f"Target column '{target_col}' not found in dataset.")

    # Initialize exclusion log
    exclusions = []
    rows_to_drop = set()

    # Step 1: Group by (material_type, surface_area_bin)
    logger.info("Performing hierarchical imputation...")
    
    # Identify rows needing imputation
    missing_mask = df[target_col].isna()
    if not missing_mask.any():
        logger.info("No missing values in pore_volume. Skipping imputation.")
    else:
        missing_indices = df[missing_mask].index.tolist()
        logger.info(f"Found {len(missing_indices)} missing values to impute.")

        # Calculate group means
        group_means = df.groupby(['material_type', 'surface_area_bin'])[target_col].mean()
        
        # Calculate material_type global means
        material_means = df.groupby('material_type')[target_col].mean()
        
        # Calculate global mean
        global_mean = df[target_col].mean()
        
        if pd.isna(global_mean):
            logger.error("Global mean is NaN. Cannot impute remaining values.")
            # If global mean is NaN, we cannot impute anything further
            exclusions.extend([
                {"index": idx, "reason": "imputation_failed", "details": "global_mean_is_nan"}
                for idx in missing_indices
            ])
            rows_to_drop.update(missing_indices)
        else:
            imputed_count = 0
            failed_count = 0

            for idx in missing_indices:
                mat_type = df.loc[idx, 'material_type']
                surf_bin = df.loc[idx, 'surface_area_bin']
                
                value = None
                impute_method = None

                # Try Group Mean
                group_key = (mat_type, surf_bin)
                if group_key in group_means.index and not pd.isna(group_means[group_key]):
                    value = group_means[group_key]
                    impute_method = "group_mean"
                
                # Try Material Mean
                if value is None and mat_type in material_means.index and not pd.isna(material_means[mat_type]):
                    value = material_means[mat_type]
                    impute_method = "material_mean"
                
                # Try Global Mean
                if value is None and not pd.isna(global_mean):
                    value = global_mean
                    impute_method = "global_mean"
                
                if value is not None:
                    df.loc[idx, target_col] = value
                    imputed_count += 1
                else:
                    # Failed to impute
                    failed_count += 1
                    exclusions.append({
                        "index": int(idx),
                        "material_type": mat_type,
                        "surface_area_bin": surf_bin,
                        "reason": "imputation_failed",
                        "details": "No valid mean found in hierarchy"
                    })
                    rows_to_drop.add(idx)

            logger.info(f"Imputation complete: {imputed_count} imputed, {failed_count} failed.")

    # Drop failed rows
    if rows_to_drop:
        logger.warning(f"Dropping {len(rows_to_drop)} rows due to imputation failure.")
        df = df.drop(index=list(rows_to_drop))
    
    # Save exclusion log
    if exclusions:
        save_imputation_log(exclusions, exclusion_log_path)
        logger.info(f"Logged {len(exclusions)} exclusions to {exclusion_log_path}")

    # Save output
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved imputed dataset to {output_path}")
    
    return df

def save_imputation_log(exclusions: List[Dict[str, Any]], log_path: str):
    """Save imputation exclusion log to JSON."""
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        # Load existing log if it exists
        existing_log = []
        if os.path.exists(log_path):
            try:
                with open(log_path, 'r') as f:
                    existing_log = json.load(f)
            except json.JSONDecodeError:
                existing_log = []
        
        # Append new exclusions
        existing_log.extend(exclusions)
        
        with open(log_path, 'w') as f:
            json.dump(existing_log, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write exclusion log: {e}")
        # Raise to ensure failure is caught
        raise

def main():
    """Main entry point for the imputation script."""
    input_file = "data/processed/target_filtered.parquet"
    output_file = "data/processed/imputed_dataset.parquet"
    log_file = "data/validation/exclusion_log.json"

    # Check if input exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run T015a-1 (filter_and_normalize) first.")
        sys.exit(1)

    ensure_directories()
    impute_pore_volume(input_file, output_file, log_file)
    logger.info("Imputation pipeline completed successfully.")

if __name__ == "__main__":
    main()