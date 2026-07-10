"""
Normalization step for HEA composition data.

Enforces sum(composition) = 1.0 for all samples and logs adjustments.
This module is part of the User Story 1 data ingestion pipeline.
"""
import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from utils.logging_config import get_logger
from utils.validators import normalize_compositions, ValidationError

# Define column naming convention for composition data
COMPOSITION_PREFIX = "comp_"
COMPOSITION_COLUMNS = [col for col in pd.read_csv if col.startswith(COMPOSITION_PREFIX)]

def get_composition_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify all columns representing elemental compositions.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of column names starting with 'comp_'
    """
    return [col for col in df.columns if col.startswith(COMPOSITION_PREFIX)]

def normalize_composition_row(row: pd.Series, comp_cols: List[str], logger: logging.Logger) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Normalize a single row's composition to sum to 1.0.
    
    Args:
        row: Single row from DataFrame
        comp_cols: List of composition column names
        logger: Logger instance for recording adjustments
        
    Returns:
        Tuple of (normalized_row, adjustment_info)
    """
    adjustment_info = {
        "original_sum": None,
        "new_sum": None,
        "adjusted": False,
        "adjustment_magnitude": 0.0
    }
    
    # Extract composition values
    comp_values = row[comp_cols].values
    
    # Calculate current sum
    current_sum = np.nansum(comp_values)
    adjustment_info["original_sum"] = float(current_sum)
    
    if current_sum == 0:
        # Handle zero-sum case - cannot normalize
        logger.warning(f"Zero composition sum detected for sample {row.get('sample_id', 'unknown')}. Skipping normalization.")
        adjustment_info["adjusted"] = False
        return row, adjustment_info
    
    # Calculate normalization factor
    normalization_factor = 1.0 / current_sum
    
    # Check if normalization is needed (allow small floating point tolerance)
    tolerance = 1e-6
    if abs(current_sum - 1.0) > tolerance:
        # Perform normalization
        normalized_values = comp_values * normalization_factor
        
        # Update row with normalized values
        for i, col in enumerate(comp_cols):
            row[col] = normalized_values[i]
        
        adjustment_info["adjusted"] = True
        adjustment_info["adjustment_magnitude"] = abs(current_sum - 1.0)
        adjustment_info["new_sum"] = 1.0
        
        logger.debug(
            f"Normalized sample {row.get('sample_id', 'unknown')}: "
            f"sum {current_sum:.6f} -> 1.0 (adjustment: {adjustment_info['adjustment_magnitude']:.6f})"
        )
    else:
        adjustment_info["new_sum"] = float(current_sum)
        logger.debug(f"Sample {row.get('sample_id', 'unknown')} already normalized (sum: {current_sum:.6f})")
    
    return row, adjustment_info

def normalize_dataframe(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Normalize composition data in a DataFrame to ensure sum = 1.0 for all samples.
    
    Args:
        df: Input DataFrame with composition columns
        logger: Optional logger instance. If None, uses default logger.
        
    Returns:
        Tuple of (normalized_df, normalization_stats)
        
    Raises:
        ValidationError: If composition columns are missing or invalid
    """
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info("Starting composition normalization")
    
    # Identify composition columns
    comp_cols = get_composition_columns(df)
    
    if not comp_cols:
        raise ValidationError("No composition columns found. Expected columns starting with 'comp_'.")
    
    logger.info(f"Found {len(comp_cols)} composition columns: {comp_cols}")
    
    # Track normalization statistics
    stats = {
        "total_samples": len(df),
        "normalized_samples": 0,
        "skipped_samples": 0,
        "zero_sum_samples": 0,
        "adjustment_magnitudes": [],
        "max_adjustment": 0.0,
        "mean_adjustment": 0.0,
        "columns_normalized": comp_cols
    }
    
    # Process each row
    normalized_rows = []
    for idx, row in df.iterrows():
        try:
            normalized_row, info = normalize_composition_row(row, comp_cols, logger)
            normalized_rows.append(normalized_row)
            
            if info["adjusted"]:
                stats["normalized_samples"] += 1
                stats["adjustment_magnitudes"].append(info["adjustment_magnitude"])
                stats["max_adjustment"] = max(stats["max_adjustment"], info["adjustment_magnitude"])
            elif info["original_sum"] == 0:
                stats["zero_sum_samples"] += 1
                stats["skipped_samples"] += 1
            else:
                stats["skipped_samples"] += 1  # Already normalized
                
        except Exception as e:
            logger.error(f"Error normalizing sample at index {idx}: {str(e)}")
            raise
    
    # Create normalized DataFrame
    normalized_df = pd.DataFrame(normalized_rows)
    
    # Calculate summary statistics
    if stats["adjustment_magnitudes"]:
        stats["mean_adjustment"] = float(np.mean(stats["adjustment_magnitudes"]))
        stats["std_adjustment"] = float(np.std(stats["adjustment_magnitudes"]))
    
    # Verify final sums
    final_sums = normalized_df[comp_cols].sum(axis=1)
    non_unit_sums = final_sums[abs(final_sums - 1.0) > 1e-6]
    
    if len(non_unit_sums) > 0:
        logger.warning(f"Found {len(non_unit_sums)} samples with non-unit sum after normalization")
        for idx in non_unit_sums.index:
            logger.warning(f"  Sample {idx}: sum = {final_sums[idx]:.6f}")
    else:
        logger.info("All samples successfully normalized to sum = 1.0")
    
    stats["verification_passed"] = len(non_unit_sums) == 0
    
    logger.info(f"Normalization complete: {stats['normalized_samples']} samples adjusted, "
               f"{stats['skipped_samples']} skipped, max adjustment: {stats['max_adjustment']:.6f}")
    
    return normalized_df, stats

def main():
    """
    Main entry point for normalization script.
    
    Reads data from data/raw/hea_samples.csv (or specified input),
    normalizes compositions, and writes to data/processed/hea_normalized.csv.
    """
    # Setup logging
    logger = get_logger(__name__)
    logger.info("Starting normalization process")
    
    # Define file paths
    input_path = "data/raw/hea_samples.csv"
    output_path = "data/processed/hea_normalized.csv"
    
    # Load input data
    try:
        logger.info(f"Loading data from {input_path}")
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} samples with {len(df.columns)} columns")
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading input file: {str(e)}")
        raise
    
    # Perform normalization
    try:
        normalized_df, stats = normalize_dataframe(df, logger)
    except ValidationError as e:
        logger.error(f"Validation error during normalization: {str(e)}")
        raise
    
    # Save normalized data
    try:
        logger.info(f"Saving normalized data to {output_path}")
        normalized_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(normalized_df)} samples to {output_path}")
    except Exception as e:
        logger.error(f"Error saving normalized data: {str(e)}")
        raise
    
    # Log summary statistics
    logger.info("Normalization Summary:")
    logger.info(f"  Total samples: {stats['total_samples']}")
    logger.info(f"  Normalized: {stats['normalized_samples']}")
    logger.info(f"  Skipped: {stats['skipped_samples']}")
    logger.info(f"  Zero-sum samples: {stats['zero_sum_samples']}")
    logger.info(f"  Max adjustment: {stats['max_adjustment']:.6f}")
    logger.info(f"  Mean adjustment: {stats['mean_adjustment']:.6f}")
    logger.info(f"  Verification passed: {stats['verification_passed']}")
    
    return normalized_df, stats

if __name__ == "__main__":
    main()
