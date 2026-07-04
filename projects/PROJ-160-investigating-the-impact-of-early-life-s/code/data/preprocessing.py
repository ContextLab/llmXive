import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from scipy import stats

from code.config import DATA_PROCESSED_DIR, DATA_RAW_DIR
from code.data.loaders import load_merged_dataset, save_dataframe

logger = logging.getLogger(__name__)

def _check_and_transform_ace_skewness(df: pd.DataFrame, column: str = "ACE") -> Tuple[pd.DataFrame, float]:
    """
    Checks the skewness of the ACE score column.
    If |skewness| > 1.0, applies a log-transformation (log1p) to the column.
    
    Args:
        df: Input DataFrame.
        column: Name of the ACE column.
        
    Returns:
        Tuple of (modified DataFrame, original skewness value).
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    
    # Drop NaNs for skewness calculation to get accurate metric
    clean_series = df[column].dropna()
    
    if len(clean_series) == 0:
        logger.warning(f"No non-null values found in column '{column}' for skewness check.")
        return df, 0.0
        
    original_skewness = float(stats.skew(clean_series))
    logger.info(f"Original skewness for '{column}': {original_skewness:.4f}")
    
    if abs(original_skewness) > 1.0:
        logger.info(f"|Skewness| ({abs(original_skewness):.4f}) > 1.0. Applying log1p transformation.")
        
        # Ensure no negative values for log transformation if using log, 
        # but log1p handles 0. If data has negatives, log1p is still valid for -1 < x.
        # Assuming ACE scores are non-negative based on typical stress metrics.
        # If strict log is needed for strictly positive, we'd use np.log. 
        # Standard practice for skewness reduction on non-negative data is log1p.
        df[f"{column}_log"] = np.log1p(df[column])
        # Update the main column to the transformed value for downstream consistency 
        # as per "apply log-transformation" implication in data prep pipelines.
        df[column] = df[f"{column}_log"]
        logger.info(f"Transformed '{column}' in place. New skewness: {float(stats.skew(df[column].dropna())):.4f}")
    else:
        logger.info(f"|Skewness| ({abs(original_skewness):.4f}) <= 1.0. No transformation applied.")
        
    return df, original_skewness

def _flag_extreme_ace_outliers(df: pd.DataFrame, column: str = "ACE", std_threshold: float = 3.0) -> pd.DataFrame:
    """
    Identifies extreme ACE outliers (>3 SD from the mean) and flags them in a new column.
    This supports downstream sensitivity analysis without auto-exclusion.
    
    Args:
        df: Input DataFrame.
        column: Name of the ACE column.
        std_threshold: Number of standard deviations to consider an outlier.
        
    Returns:
        DataFrame with a new boolean column '{column}_outlier_flag'.
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")
    
    clean_series = df[column].dropna()
    
    if len(clean_series) < 2:
        logger.warning(f"Insufficient data to calculate outliers for '{column}'.")
        df[f"{column}_outlier_flag"] = False
        return df
    
    mean_val = clean_series.mean()
    std_val = clean_series.std()
    
    if std_val == 0:
        logger.warning(f"Standard deviation for '{column}' is 0. No outliers can be flagged.")
        df[f"{column}_outlier_flag"] = False
        return df
    
    lower_bound = mean_val - (std_threshold * std_val)
    upper_bound = mean_val + (std_threshold * std_val)
    
    # Flag rows where ACE is outside the bounds
    df[f"{column}_outlier_flag"] = (df[column] < lower_bound) | (df[column] > upper_bound)
    
    outlier_count = df[f"{column}_outlier_flag"].sum()
    total_count = len(df)
    logger.info(
        f"Flagged {outlier_count} outliers for '{column}' (>{std_threshold} SD). "
        f"Bounds: [{lower_bound:.4f}, {upper_bound:.4f}]. "
        f"Total rows: {total_count}, Retention: 100% (no exclusion)."
    )
    
    return df

def run_preprocessing_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    skip_acquisition: bool = False
) -> Dict[str, Any]:
    """
    Runs the full preprocessing pipeline:
    1. Loads merged dataset (or from input_path).
    2. Handles missing ACE/MRI (T015 logic - assumed done or handled by loader).
    3. Normalizes volumes by ICV (T016 logic).
    4. Checks ACE skewness and applies log-transformation if |skew| > 1.0 (T017).
    5. Flags extreme ACE outliers (>3 SD) for sensitivity analysis (T018).
    6. Saves to output_path.
    
    Args:
        input_path: Path to input CSV. Defaults to processed intermediate if available.
        output_path: Path to save final cleaned dataset.
        skip_acquisition: If True, expects data to already exist in raw/processed.
        
    Returns:
        Dictionary with pipeline stats and paths.
    """
    # Ensure output directory exists
    Path(DATA_PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = os.path.join(DATA_PROCESSED_DIR, "cleaned_dataset.csv")
        
    logger.info(f"Starting preprocessing pipeline. Output: {output_path}")
    
    # Load Data
    # Assuming T015 and T016 are integrated into the flow or previous steps
    # Here we implement the T017 and T018 specific logic on top of the expected state.
    
    try:
        df = load_merged_dataset()
    except Exception as e:
        logger.error(f"Failed to load merged dataset: {e}")
        raise
        
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} rows.")
    
    # T016 Logic: Normalize volumes by ICV if not already done
    # Expected columns: CA3, DG, Subiculum, ICV
    volume_cols = ["CA3", "DG", "Subiculum"]
    for col in volume_cols:
        if col in df.columns and "ICV" in df.columns:
            norm_col = f"{col}_Normalized"
            # Avoid division by zero
            df[norm_col] = np.where(df["ICV"] > 0, df[col] / df["ICV"], np.nan)
            logger.info(f"Normalized {col} by ICV into {norm_col}")
        else:
            logger.warning(f"Skipping normalization for {col}: missing source or ICV column.")
            
    # T017 Logic: Check ACE skewness and log-transform
    ace_col = "ACE"
    skew_val = 0.0
    if ace_col in df.columns:
        df, skew_val = _check_and_transform_ace_skewness(df, column=ace_col)
    else:
        logger.warning(f"ACE column not found. Skipping skewness check.")
        
    # T018 Logic: Flag extreme ACE outliers (>3 SD)
    if ace_col in df.columns:
        df = _flag_extreme_ace_outliers(df, column=ace_col, std_threshold=3.0)
    else:
        logger.warning(f"ACE column not found. Skipping outlier flagging.")
    
    # Save results
    save_dataframe(df, output_path)
    final_count = len(df)
    
    logger.info(f"Pipeline complete. Rows: {initial_count} -> {final_count}")
    logger.info(f"Saved to: {output_path}")
    
    return {
        "input_rows": initial_count,
        "output_rows": final_count,
        "output_path": output_path,
        "ace_skewness_initial": skew_val,
        "columns": list(df.columns)
    }

if __name__ == "__main__":
    # Basic execution entry point for testing
    logging.basicConfig(level=logging.INFO)
    result = run_preprocessing_pipeline()
    print(f"Pipeline finished: {result}")