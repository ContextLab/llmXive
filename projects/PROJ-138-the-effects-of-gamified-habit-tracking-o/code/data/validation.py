"""
Data validation and consent checking.
"""
import os
import json
import pandas as pd
import pingouin as pg
from typing import List, Optional
from code.utils.logging import pipeline_logger

CONSENT_DIR = "data/consent"

def check_consent() -> bool:
    """
    Verify consent artifacts exist.
    
    Logic:
    - If real data is present, halt if `data/consent/` is missing (FR-010).
    - If synthetic data is used, generate a synthetic consent artifact.
    
    Returns:
        True if consent is verified or generated.
        
    Raises:
        FileNotFoundError: If real data is expected but consent is missing.
    """
    # Ensure the consent directory exists
    if not os.path.exists(CONSENT_DIR):
        os.makedirs(CONSENT_DIR, exist_ok=True)
    
    consent_file = os.path.join(CONSENT_DIR, "consent_record.json")
    synthetic_file = os.path.join(CONSENT_DIR, "synthetic_consent_record.json")
    
    # Check if a synthetic consent record already exists
    if os.path.exists(synthetic_file):
        pipeline_logger.info("Synthetic consent record found.")
        return True
    
    # Check if a real consent record already exists
    if os.path.exists(consent_file):
        pipeline_logger.info("Real consent record found.")
        return True
    
    # If no consent file exists, determine if we are in a synthetic context
    # based on environment variable. If so, generate the artifact.
    if os.getenv("USE_SYNTHETIC_DATA", "false").lower() == "true":
        record = {
            "type": "synthetic",
            "description": "This dataset is synthetically generated for research purposes.",
            "approval": "Research ethics approval for synthetic data simulation (FR-010)",
            "generated_at": pd.Timestamp.now().isoformat(),
            "approved_by": "Automated Pipeline (Synthetic Mode)"
        }
        with open(synthetic_file, "w") as f:
            json.dump(record, f, indent=2)
        pipeline_logger.info(f"Generated synthetic consent record at {synthetic_file}")
        return True
    
    # If we are here, no consent exists and we are not in synthetic mode.
    # Per FR-010, halt execution if real data is expected but consent is missing.
    pipeline_logger.error("Consent record missing. Halting execution as per FR-010.")
    raise FileNotFoundError(
        f"Consent record not found in {CONSENT_DIR}. "
        "Set USE_SYNTHETIC_DATA=true to generate a synthetic consent record, "
        "or provide a valid consent_record.json for real data."
    )

def calculate_cronbach_alpha(df: pd.DataFrame, item_columns: List[str]) -> float:
    """
    Calculate Cronbach's alpha for a set of items.
    
    This function calculates the internal consistency reliability (Cronbach's alpha)
    for a set of scale items using the `pingouin` library. It handles missing data
    by excluding rows with any missing values in the specified item columns from the
    calculation, and logs the count of excluded rows.
    
    Args:
        df: DataFrame containing the item columns.
        item_columns: List of column names representing scale items.
        
    Returns:
        Cronbach's alpha value (float). Returns 0.0 if insufficient data remains
        after excluding missing values.
        
    Raises:
        ValueError: If `item_columns` is empty or contains columns not in `df`.
    """
    if not item_columns:
        raise ValueError("item_columns list cannot be empty.")
    
    missing_cols = set(item_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Columns not found in DataFrame: {missing_cols}")
    
    # Filter out rows with missing data for these columns
    # dropna() on the subset excludes any row with NaN in any of the item_columns
    subset = df[item_columns].dropna()
    excluded_count = len(df) - len(subset)
    
    if excluded_count > 0:
        pipeline_logger.warning(f"Excluded {excluded_count} rows due to missing values in Cronbach's alpha calculation.")
    
    if subset.empty:
        pipeline_logger.warning("No valid data remaining for Cronbach's alpha calculation after excluding missing values.")
        return 0.0
    
    try:
        result = pg.cronbach_alpha(data=subset)
        # pg.cronbach_alpha returns a tuple (alpha, ci) or a scalar depending on version,
        # but typically returns a scalar alpha in recent versions or a dict-like object.
        # Checking the return type to be safe.
        if isinstance(result, tuple):
            alpha_val = result[0]
        elif isinstance(result, dict):
            alpha_val = result['alpha']
        else:
            alpha_val = float(result)
        
        pipeline_logger.info(f"Cronbach's alpha calculated: {alpha_val:.4f} (excluded {excluded_count} rows)")
        return alpha_val
    except Exception as e:
        pipeline_logger.error(f"Error calculating Cronbach's alpha: {e}")
        raise

def validate_schema(df: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Validate that a DataFrame contains all required columns.
    
    Args:
        df: DataFrame to validate.
        required_columns: List of required column names.
        
    Raises:
        ValueError: If any required column is missing.
    """
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    pipeline_logger.info("Schema validation passed.")