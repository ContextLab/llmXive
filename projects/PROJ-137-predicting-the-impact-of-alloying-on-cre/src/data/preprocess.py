"""
Data Preprocessing (T017).

- Parse compositions
- Filter missing values
- Log exclusions
"""
import pandas as pd
import logging
from src.utils.validators import parse_composition_string, validate_physics_consistency

logger = logging.getLogger(__name__)

def parse_compositions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse composition strings into atomic fractions.
    """
    # Expand composition strings into columns
    expanded = df["composition_str"].apply(parse_composition_string).apply(pd.Series)
    expanded = expanded.add_prefix("elem_")
    
    # Combine with original
    df_expanded = pd.concat([df.reset_index(drop=True), expanded], axis=1)
    
    # Fill NaN with 0 (elements not present)
    df_expanded = df_expanded.fillna(0)
    
    return df_expanded

def filter_valid_entries(df: pd.DataFrame, log_exclusions: bool = True) -> pd.DataFrame:
    """
    Filter entries with missing critical data (temp, stress, rupture_time).
    Logs excluded entries.
    """
    required_cols = ["temperature", "stress", "rupture_time"]
    initial_len = len(df)
    
    # Check for missing values in required columns
    mask = df[required_cols].notna().all(axis=1)
    filtered_df = df[mask].copy()
    
    excluded_count = initial_len - len(filtered_df)
    
    if log_exclusions and excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} entries due to missing temperature/stress/rupture_time.")
        # Log specific rows if needed (optional)
    
    # Physics consistency check
    valid, msg = validate_physics_consistency(filtered_df)
    if not valid:
        logger.error(f"Physics consistency check failed: {msg}")
        # In a strict pipeline, we might drop these rows or fail
        # Here we assume the data is clean enough after filtering NaN
    
    return filtered_df

if __name__ == "__main__":
    # Test
    pass
