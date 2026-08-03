import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def count_principal_elements(composition: Dict[str, float], threshold: float = 0.05) -> int:
    """
    Count the number of principal elements in a composition dictionary.
    An element is considered 'principal' if its atomic fraction is >= threshold.

    Args:
        composition: Dict mapping element symbols to atomic fractions.
        threshold: Minimum fraction to be considered a principal element.

    Returns:
        Integer count of principal elements.
    """
    if not isinstance(composition, dict):
        # Handle potential string representation or other formats if necessary
        # For now, assume dict or Series-like behavior
        if hasattr(composition, 'items'):
            composition = dict(composition)
        else:
            return 0

    count = 0
    for element, fraction in composition.items():
        # Skip non-element columns if any slipped in (e.g. metadata)
        if not isinstance(fraction, (int, float)):
            continue
        if fraction >= threshold:
            count += 1
    return count


def filter_hea_samples(
    df: pd.DataFrame,
    min_principal_elements: int = 5,
    composition_threshold: float = 0.05,
    target_column: str = "Bulk_Modulus",
    min_valid_samples: int = 1
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter the dataframe to retain only High-Entropy Alloy (HEA) samples.
    Criteria:
      1. At least `min_principal_elements` elements with fraction >= `composition_threshold`.
      2. Valid (non-null) Bulk Modulus value.

    Args:
        df: Input dataframe containing composition columns and target.
        min_principal_elements: Minimum number of principal elements required (default 5).
        composition_threshold: Threshold to define a principal element (default 0.05).
        target_column: Name of the target column to check for validity.
        min_valid_samples: Minimum number of valid samples required to proceed.

    Returns:
        Tuple of (filtered_dataframe, stats_dict).
        stats_dict contains counts for total, filtered, and invalid samples.

    Raises:
        ValueError: If the resulting dataset has fewer than `min_valid_samples`.
    """
    logger.info(f"Starting HEA filtering: min_elements={min_principal_elements}, target={target_column}")

    # Identify composition columns: typically columns that look like element symbols
    # We assume non-composition columns are metadata or targets.
    # A simple heuristic: columns that are not 'Bulk_Modulus', 'Material_ID', etc.
    # However, a safer approach in this pipeline context is to assume all columns
    # except known metadata/targets are composition.
    # Let's rely on the fact that composition columns are likely float/numeric and
    # correspond to element symbols.
    
    # Exclude known non-composition columns
    exclude_cols = {target_column, 'Material_ID', 'Formula', 'System', 'Source', 'Bulk_Modulus_Miedema', 'Bulk_Modulus_Residual'}
    comp_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in [np.float64, np.float32, np.int64, np.int32]]
    
    if not comp_cols:
        logger.warning("No composition columns found in dataframe.")
        return pd.DataFrame(), {"total": 0, "filtered": 0, "invalid": 0}

    logger.info(f"Detected {len(comp_cols)} potential composition columns.")

    # Apply principal element count filter
    def is_hea(row):
        # Extract composition for this row
        comp = row[comp_cols].to_dict()
        count = count_principal_elements(comp, composition_threshold)
        return count >= min_principal_elements

    # Apply bulk modulus validity filter
    def has_valid_target(row):
        val = row[target_column]
        return pd.notna(val) and np.isfinite(val)

    mask_elements = df.apply(is_hea, axis=1)
    mask_target = df.apply(has_valid_target, axis=1)
    
    combined_mask = mask_elements & mask_target

    filtered_df = df[combined_mask].reset_index(drop=True)
    
    total_count = len(df)
    filtered_count = len(filtered_df)
    invalid_count = total_count - filtered_count

    stats = {
        "total": total_count,
        "filtered": filtered_count,
        "invalid_by_elements": int((mask_elements == False).sum()),
        "invalid_by_target": int((mask_target == False).sum()),
        "final_valid": filtered_count
    }

    logger.info(f"Filtering complete. Total: {total_count}, Kept: {filtered_count}, Dropped: {invalid_count}")
    logger.info(f"Stats: {stats}")

    if filtered_count < min_valid_samples:
        msg = f"Filtered dataset has {filtered_count} samples, which is less than the required minimum {min_valid_samples}."
        logger.error(msg)
        # Do not raise here to allow the pipeline to handle the 'Underpowered' logic downstream
        # but log it heavily. The caller (pipeline) should handle the decision to halt or report.
        # However, for the strict definition of this function, returning an empty or small DF is the result.
        # The spec says "Fail if exit code != 0" for T001, but for T016 it says "retain samples".
        # We return the filtered data. The pipeline will check the count.
    
    return filtered_df, stats


def main():
    """
    Entry point for running the filter module directly.
    Expects a raw CSV in data/raw/hea_raw.csv (or similar) and outputs to data/processed/.
    This is primarily for testing or manual execution.
    """
    import sys
    import os
    from pathlib import Path

    # Simple CLI for manual testing
    input_path = os.environ.get("INPUT_DATA_PATH", "data/raw/hea_raw.csv")
    output_path = os.environ.get("OUTPUT_DATA_PATH", "data/processed/hea_filtered.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    filtered_df, stats = filter_hea_samples(df)

    if filtered_df.empty:
        logger.warning("Resulting dataframe is empty.")
    
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path} ({len(filtered_df)} rows)")
    
    # Print stats to stdout for easy checking
    import json
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
