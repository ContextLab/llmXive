"""
Imputation module for handling missing pore volume data.
Implements hierarchical imputation logic based on material type and surface area bins.
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
    """Ensure required output directories exist."""
    validation_dir = Path("data/validation")
    validation_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {validation_dir}")

def impute_pore_volume(
    df: pd.DataFrame,
    surface_area_bin_col: str = 'surface_area_bin',
    material_type_col: str = 'material_type',
    target_col: str = 'pore_volume',
    exclusion_log_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Impute missing pore_volume values using a hierarchical strategy:
    1. Group by (material_type, surface_area_bin) -> assign group mean.
    2. If group is empty, assign material_type global mean.
    3. If material_type is missing, assign global dataset mean.
    4. If imputation fails (e.g., all NaN in group), exclude row and log.

    Args:
        df: Input DataFrame with potential missing values in target_col.
        surface_area_bin_col: Column name for surface area bins.
        material_type_col: Column name for material types.
        target_col: Column name of the target to impute.
        exclusion_log_path: Path to write exclusion logs. If None, uses default.

    Returns:
        Tuple of (imputed DataFrame, list of excluded row records).
    """
    if exclusion_log_path is None:
        exclusion_log_path = Path("data/validation/exclusion_log.json")
    
    ensure_directories()

    # Work on a copy to avoid SettingWithCopyWarning
    df_work = df.copy()
    excluded_rows = []
    
    # Identify rows needing imputation
    missing_mask = df_work[target_col].isna()
    if not missing_mask.any():
        logger.info("No missing values found in target column. No imputation needed.")
        return df_work, excluded_rows

    missing_indices = df_work[missing_mask].index.tolist()
    logger.info(f"Found {len(missing_indices)} rows with missing {target_col}.")

    # Pre-calculate global mean (excluding NaN)
    global_mean = df_work[target_col].mean()
    if pd.isna(global_mean):
        logger.warning("Global mean is NaN. Cannot impute if all data is missing.")
        # If global mean is NaN, we can't impute anything, so exclude all missing
        for idx in missing_indices:
            row_data = df_work.loc[idx].to_dict()
            row_data['exclusion_reason'] = 'Global mean is NaN, cannot impute'
            excluded_rows.append(row_data)
        df_work.loc[missing_indices, target_col] = np.nan # Keep as NaN or drop later
        return df_work, excluded_rows

    # Pre-calculate material_type global means
    # Group by material_type and calculate mean for target_col
    material_means = df_work.groupby(material_type_col)[target_col].mean()
    # Handle cases where material_type is NaN
    material_means = material_means.dropna()

    # Define binning logic if not already binned
    # Assuming surface_area_bin_col is already a categorical or string bin representation
    # If it's numeric, we might need to bin it, but task implies it's pre-binned or we bin here.
    # Let's assume it's already binned or we treat unique values as bins.
    
    # We need to handle the grouping carefully.
    # Strategy: Iterate through missing rows and find the best mean.
    
    rows_to_drop = []
    
    for idx in missing_indices:
        row = df_work.loc[idx]
        mat_type = row[material_type_col]
        surf_bin = row[surface_area_bin_col]
        
        impute_value = None
        reason = None
        
        # Level 1: Group mean (material_type, surface_area_bin)
        # We filter the dataframe to the specific group
        # Note: We must exclude the current row if it was in the group, but since it's NaN, it doesn't affect mean
        group_mask = (
            (df_work[material_type_col] == mat_type) & 
            (df_work[surface_area_bin_col] == surf_bin)
        )
        group_data = df_work.loc[group_mask, target_col]
        
        # Check if group has any non-NaN values
        if not group_data.isna().all():
            group_mean = group_data.mean()
            if not pd.isna(group_mean):
                impute_value = group_mean
                reason = f"Group mean (type={mat_type}, bin={surf_bin})"
        
        # Level 2: Material type global mean
        if impute_value is None:
            if pd.notna(mat_type) and mat_type in material_means.index:
                mat_mean = material_means[mat_type]
                if not pd.isna(mat_mean):
                    impute_value = mat_mean
                    reason = f"Material type global mean (type={mat_type})"
        
        # Level 3: Global dataset mean
        if impute_value is None:
            if not pd.isna(global_mean):
                impute_value = global_mean
                reason = "Global dataset mean"
        
        if impute_value is not None:
            df_work.loc[idx, target_col] = impute_value
            logger.debug(f"Imputed row {idx} with {reason}: {impute_value}")
        else:
            # Imputation failed
            row_data = row.to_dict()
            row_data['exclusion_reason'] = 'Imputation failed: No valid mean found in hierarchy'
            excluded_rows.append(row_data)
            rows_to_drop.append(idx)
            logger.warning(f"Failed to impute row {idx}. Marked for exclusion.")

    # Remove rows that failed imputation from the DataFrame
    if rows_to_drop:
        df_work = df_work.drop(index=rows_to_drop)
        logger.info(f"Dropped {len(rows_to_drop)} rows due to imputation failure.")

    # Log exclusions to file
    if excluded_rows:
        with open(exclusion_log_path, 'w') as f:
            json.dump(excluded_rows, f, indent=2, default=str)
        logger.info(f"Logged {len(excluded_rows)} excluded rows to {exclusion_log_path}")
    
    return df_work, excluded_rows

def save_imputation_log(excluded_rows: List[Dict[str, Any]], log_path: Path):
    """
    Save the list of excluded rows to a JSON file.
    """
    ensure_directories()
    with open(log_path, 'w') as f:
        json.dump(excluded_rows, f, indent=2, default=str)
    logger.info(f"Saved imputation exclusion log to {log_path}")

def main():
    """
    Main entry point for testing imputation logic.
    Loads data from data/raw/merged_dataset.parquet (if exists),
    performs imputation, and saves results.
    """
    input_path = Path("data/raw/merged_dataset.parquet")
    output_path = Path("data/processed/imputed_dataset.parquet")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Cannot run imputation.")
        # In a real pipeline, this might raise an error or fetch data
        # For now, we just log and exit to avoid synthetic data generation
        sys.exit(1)

    try:
        logger.info(f"Loading data from {input_path}...")
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} rows.")

        # Ensure columns exist
        required_cols = ['pore_volume', 'material_type', 'surface_area_bin']
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            sys.exit(1)

        # Perform imputation
        imputed_df, excluded_rows = impute_pore_volume(df)
        
        logger.info(f"Imputation complete. Rows before: {len(df)}, Rows after: {len(imputed_df)}")
        
        # Save imputed dataset
        output_path.parent.mkdir(parents=True, exist_ok=True)
        imputed_df.to_parquet(output_path, index=False)
        logger.info(f"Saved imputed dataset to {output_path}")

        # Save exclusion log (already done inside impute_pore_volume, but ensuring path)
        log_path = Path("data/validation/exclusion_log.json")
        if excluded_rows:
            save_imputation_log(excluded_rows, log_path)
        
    except Exception as e:
        logger.error(f"Error during imputation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()