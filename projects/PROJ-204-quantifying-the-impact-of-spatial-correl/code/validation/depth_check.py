"""
Depth resolution validation module.

Implements FR-008: Flags samples where bulk EDS may not correlate with surface PCE
by checking depth resolution metadata and layer thickness information.
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Default thresholds (configurable via config if needed)
DEFAULT_MAX_BULK_DEPTH = 2.0  # micrometers - typical EDS bulk analysis depth
DEFAULT_SURFACE_LAYER_MAX = 0.1  # micrometers - typical perovskite surface layer
DEFAULT_DEPTH_RATIO_THRESHOLD = 0.5  # If bulk_depth / surface_layer > threshold, flag


def load_sample_metadata(metadata_file: Path) -> pd.DataFrame:
    """
    Load sample metadata containing depth information.

    Args:
        metadata_file: Path to CSV containing sample metadata

    Returns:
        DataFrame with sample metadata including depth fields
    """
    if not metadata_file.exists():
        logger.warning(f"Metadata file not found: {metadata_file}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(metadata_file)
        required_cols = ['sample_id', 'bulk_depth_um', 'surface_layer_um']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.error(f"Missing required metadata columns: {missing_cols}")
            return pd.DataFrame()

        return df
    except Exception as e:
        logger.error(f"Failed to load metadata from {metadata_file}: {e}")
        return pd.DataFrame()


def validate_depth_resolution(
    sample_id: str,
    bulk_depth: Optional[float],
    surface_layer: Optional[float],
    max_bulk_depth: float = DEFAULT_MAX_BULK_DEPTH,
    depth_ratio_threshold: float = DEFAULT_DEPTH_RATIO_THRESHOLD
) -> Tuple[bool, str]:
    """
    Validate if depth resolution is appropriate for surface PCE correlation.

    Args:
        sample_id: Unique sample identifier
        bulk_depth: EDS bulk analysis depth in micrometers
        surface_layer: Surface active layer thickness in micrometers
        max_bulk_depth: Maximum acceptable bulk depth
        depth_ratio_threshold: Ratio threshold for flagging

    Returns:
        Tuple of (is_valid, reason_string)
    """
    # Check for missing data
    if bulk_depth is None or surface_layer is None:
        return False, f"Missing depth metadata for {sample_id}"

    # Check if bulk depth is within acceptable range
    if bulk_depth > max_bulk_depth:
        return False, f"Bulk depth {bulk_depth:.2f}um exceeds max {max_bulk_depth}um"

    # Check ratio of bulk depth to surface layer
    if surface_layer > 0:
        ratio = bulk_depth / surface_layer
        if ratio > depth_ratio_threshold:
            return False, f"Depth ratio {ratio:.2f} exceeds threshold {depth_ratio_threshold}"

    return True, "Depth resolution appropriate for surface correlation"


def apply_depth_check(
    dataset_path: Path,
    metadata_path: Path,
    output_path: Path
) -> pd.DataFrame:
    """
    Apply depth resolution validation to entire dataset.

    Args:
        dataset_path: Path to unified dataset CSV
        metadata_path: Path to metadata CSV with depth information
        output_path: Path to write results with depth_flag

    Returns:
        DataFrame with depth_flag column added
    """
    # Load datasets
    try:
        dataset = pd.read_csv(dataset_path)
    except Exception as e:
        logger.error(f"Failed to load dataset from {dataset_path}: {e}")
        raise

    if dataset.empty:
        logger.warning("Dataset is empty, nothing to validate")
        return dataset

    # Load metadata
    metadata = load_sample_metadata(metadata_path)
    if metadata.empty:
        logger.warning("No metadata available, setting all flags to missing")
        dataset['depth_flag'] = 'missing_metadata'
        dataset.to_csv(output_path, index=False)
        return dataset

    # Merge datasets
    merged = dataset.merge(
        metadata[['sample_id', 'bulk_depth_um', 'surface_layer_um']],
        on='sample_id',
        how='left'
    )

    # Apply validation
    flags = []
    reasons = []

    for _, row in merged.iterrows():
        sample_id = row['sample_id']
        bulk_depth = row.get('bulk_depth_um')
        surface_layer = row.get('surface_layer_um')

        is_valid, reason = validate_depth_resolution(
            sample_id, bulk_depth, surface_layer
        )

        if is_valid:
            flags.append('valid')
        else:
            flags.append('depth_conflict')
        reasons.append(reason)

    merged['depth_flag'] = flags
    merged['depth_reason'] = reasons

    # Log summary
    flag_counts = merged['depth_flag'].value_counts()
    logger.info(f"Depth validation complete: {dict(flag_counts)}")

    # Save results
    merged.to_csv(output_path, index=False)
    logger.info(f"Results written to {output_path}")

    return merged


def check_depth_conflicts(
    dataset: pd.DataFrame,
    flag_column: str = 'depth_flag'
) -> Dict[str, Any]:
    """
    Analyze depth flag distribution and identify conflict patterns.

    Args:
        dataset: DataFrame with depth_flag column
        flag_column: Name of the flag column

    Returns:
        Dictionary with conflict statistics
    """
    if flag_column not in dataset.columns:
        return {'error': f"Column {flag_column} not found"}

    flag_counts = dataset[flag_column].value_counts().to_dict()
    total = len(dataset)
    conflict_count = flag_counts.get('depth_conflict', 0)

    return {
        'total_samples': total,
        'valid_samples': flag_counts.get('valid', 0),
        'conflict_samples': conflict_count,
        'missing_metadata': flag_counts.get('missing_metadata', 0),
        'conflict_rate': conflict_count / total if total > 0 else 0,
        'flag_distribution': flag_counts
    }


def main():
    """
    Main entry point for depth resolution validation.

    Reads from data/processed/unified_dataset.csv and data/raw/metadata.csv
    (or similar paths) and outputs to data/processed/unified_dataset_depth.csv
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Default paths (can be overridden via command line args in future)
    dataset_path = Path('data/processed/unified_dataset.csv')
    metadata_path = Path('data/raw/metadata.csv')
    output_path = Path('data/processed/unified_dataset_depth.csv')

    if not dataset_path.exists():
        logger.error(f"Dataset not found: {dataset_path}")
        logger.error("Run data ingestion first to create unified_dataset.csv")
        return

    if not metadata_path.exists():
        logger.warning(f"Metadata not found: {metadata_path}")
        logger.warning("Creating dataset with missing metadata flags")
        # Create output with missing flags
        try:
            dataset = pd.read_csv(dataset_path)
            dataset['depth_flag'] = 'missing_metadata'
            dataset['depth_reason'] = 'No metadata file found'
            dataset.to_csv(output_path, index=False)
            logger.info(f"Created {output_path} with missing metadata flags")
            return
        except Exception as e:
            logger.error(f"Failed to create output: {e}")
            return

    # Run validation
    result = apply_depth_check(dataset_path, metadata_path, output_path)

    # Print summary
    summary = check_depth_conflicts(result)
    logger.info(f"Depth validation summary: {summary}")


if __name__ == '__main__':
    main()
