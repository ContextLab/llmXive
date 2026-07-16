"""
Rating validation utilities.
Calculates reliability metrics (Cohen's Kappa / Krippendorff's Alpha) and validates schemas.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import krippendorff
from scipy.stats import cohen_kappa

logger = logging.getLogger(__name__)

def load_ratings_for_validator(path: Path) -> pd.DataFrame:
    """Loads ratings for validation."""
    if not path.exists():
        raise FileNotFoundError(f"Ratings file not found: {path}")
    df = pd.read_csv(path)
    required = {'conversation_id', 'authenticity_score', 'rater_id'}
    if not required.issubset(df.columns):
        raise ValueError(f"Ratings file missing required columns: {required - set(df.columns)}")
    return df

def calculate_krippendorff_alpha(df: pd.DataFrame, value_col: str = 'authenticity_score', 
                                 item_col: str = 'conversation_id', 
                                 rater_col: str = 'rater_id') -> float:
    """
    Calculates Krippendorff's Alpha for inter-rater reliability.
    Falls back to Cohen's Kappa if only 2 raters are present for all items.
    """
    # Pivot to get rater x item matrix
    try:
        matrix = df.pivot_table(index=item_col, columns=rater_col, values=value_col, aggfunc='first')
    except ValueError as e:
        logger.warning(f"Could not pivot data for Alpha: {e}. Attempting Kappa.")
        return calculate_cohen_kappa(df, value_col, item_col, rater_col)

    # Convert to numpy array, handling NaNs (krippendorff handles missing data)
    alpha = krippendorff.alpha(reliability_data=matrix, level_of_measurement='ordinal')
    return alpha

def calculate_cohen_kappa(df: pd.DataFrame, value_col: str = 'authenticity_score', 
                          item_col: str = 'conversation_id', 
                          rater_col: str = 'rater_id') -> float:
    """
    Calculates Cohen's Kappa for exactly two raters.
    """
    # Check if exactly two raters
    raters = df[rater_col].unique()
    if len(raters) != 2:
        logger.warning(f"Expected 2 raters for Cohen's Kappa, found {len(raters)}. Using Alpha.")
        return calculate_krippendorff_alpha(df, value_col, item_col, rater_col)
    
    rater_a, rater_b = raters
    df_a = df[df[rater_col] == rater_a].set_index(item_col)[value_col]
    df_b = df[df[rater_col] == rater_b].set_index(item_col)[value_col]
    
    # Align indices
    common_idx = df_a.index.intersection(df_b.index)
    if len(common_idx) == 0:
        raise ValueError("No common items between raters for Kappa calculation.")
        
    kappa, _ = cohen_kappa(df_a.loc[common_idx], df_b.loc[common_idx])
    return kappa

def write_reliability_metrics(kappa_value: float, sample_size: int, output_path: Path):
    """Writes reliability metrics to JSON."""
    metrics = {
        "kappa_value": kappa_value,
        "sample_size": sample_size,
        "threshold_target": 0.6,
        "status": "passed" if kappa_value >= 0.6 else "failed"
    }
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Reliability metrics written to {output_path}")

def validate_ratings(df: pd.DataFrame, target_kappa: float = 0.6) -> bool:
    """
    Validates ratings against the target kappa.
    Returns True if passed, False otherwise.
    """
    # Calculate reliability
    try:
        reliability = calculate_krippendorff_alpha(df)
    except Exception as e:
        logger.error(f"Reliability calculation failed: {e}")
        return False
        
    logger.info(f"Calculated reliability (Alpha/Kappa): {reliability:.4f}")
    return reliability >= target_kappa

def main():
    """Entry point for validation script."""
    # This would be called by the pipeline
    pass