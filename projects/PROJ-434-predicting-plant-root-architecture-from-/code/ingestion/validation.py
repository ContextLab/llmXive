import os
import sys
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import pandas as pd

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.logging_utils import (
    setup_logging,
    get_logger,
    log_validation_failure
)
from utils.exceptions import DataQualityError

def calculate_match_proportion(df: pd.DataFrame, soil_cols: List[str]) -> float:
    """
    Calculate the proportion of rows with valid soil data for all predictors.
    
    Args:
        df: DataFrame containing soil columns.
        soil_cols: List of soil column names to check.
    
    Returns:
        Proportion of valid rows (0.0 to 1.0).
    """
    if not soil_cols:
        return 1.0
    
    valid_mask = df[soil_cols].notna().all(axis=1)
    return valid_mask.sum() / len(df) if len(df) > 0 else 0.0

def filter_valid_rows(
    df: pd.DataFrame,
    soil_cols: List[str]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Filter out rows with missing soil data and log them.
    
    Args:
        df: Input DataFrame.
        soil_cols: List of soil column names to validate.
    
    Returns:
        Tuple of (filtered DataFrame, list of excluded row details).
    """
    logger = get_logger(__name__)
    
    if not soil_cols:
        return df, []
    
    valid_mask = df[soil_cols].notna().all(axis=1)
    valid_df = df[valid_mask].copy()
    invalid_df = df[~valid_mask]
    
    excluded_rows = []
    
    for idx, row in invalid_df.iterrows():
        missing_fields = [col for col in soil_cols if pd.isna(row.get(col))]
        reason = f"missing soil data: {', '.join(missing_fields)}"
        
        # Log the exclusion
        log_excluded_record(
            logger,
            record_id=str(idx),
            reason=reason,
            details={
                'lat': row.get('latitude'),
                'lon': row.get('longitude'),
                'species': row.get('species_name')
            }
        )
        
        excluded_rows.append({
            'row_id': idx,
            'reason': reason,
            'missing_fields': missing_fields
        })
    
    logger.info(f"Filtered {len(invalid_df)} rows with missing soil data. Remaining: {len(valid_df)}")
    
    return valid_df, excluded_rows

def validate_soil_data_coverage(
    df: pd.DataFrame,
    soil_cols: List[str],
    threshold: float = 0.90,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Validate that the proportion of rows with complete soil data meets the threshold.
    
    Args:
        df: DataFrame to validate.
        soil_cols: List of soil column names.
        threshold: Minimum required match proportion.
        logger: Optional logger instance.
    
    Returns:
        True if validation passes, False otherwise.
    
    Raises:
        DataQualityError: If the proportion is below the threshold.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    proportion = calculate_match_proportion(df, soil_cols)
    
    if proportion < threshold:
        msg = f"Match proportion {proportion:.4f} is below threshold {threshold}"
        log_validation_failure(
            logger,
            metric_name="soil_data_match_proportion",
            observed_value=proportion,
            threshold=threshold,
            message=msg
        )
        raise DataQualityError(msg)
    
    logger.info(f"Validation passed: soil data match proportion {proportion:.4f} >= {threshold}")
    return True

def main():
    """
    Main execution flow for validation.
    """
    # Setup logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "validation_process.log"
    setup_logging(str(log_file))
    logger = get_logger(__name__)
    
    # Example usage (would be called with real data in pipeline)
    # df = pd.read_csv("data/processed/merged_dataset.csv")
    # soil_cols = ['soil_n', 'soil_p', 'soil_k', 'soil_ph']
    # validate_soil_data_coverage(df, soil_cols, threshold=0.90, logger=logger)
    
    logger.info("Validation module loaded. Call functions with real data.")

if __name__ == "__main__":
    main()