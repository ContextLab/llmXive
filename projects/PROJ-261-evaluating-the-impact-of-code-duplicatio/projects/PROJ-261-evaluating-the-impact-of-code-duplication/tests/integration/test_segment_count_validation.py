"""
Integration test for SC-003: Segment Count Validation.

This test validates that the pipeline has processed at least 1000 code segments
with valid clone density and perplexity measurements.

SC-003 Requirement:
- At least 1000 code segments must be processed
- Each segment must have valid clone density (not NaN, not infinite, 0 <= density <= 1)
- Each segment must have valid perplexity (not NaN, not infinite, > 0)

Test must run after T021 (main.py pipeline) has completed successfully.
"""

import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Output file paths (from T021 main.py)
CLONE_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "clone_metrics.csv"
PERPLEXITY_SCORES_PATH = PROJECT_ROOT / "data" / "processed" / "perplexity_scores.csv"

# SC-003 threshold
MIN_SEGMENTS_REQUIRED = 1000


def check_file_exists(file_path: Path) -> None:
    """Assert that the output file exists."""
    assert file_path.exists(), f"Output file does not exist: {file_path}"
    logger.info(f"✓ File exists: {file_path}")


def check_file_not_empty(file_path: Path) -> int:
    """Assert that the output file is not empty and return row count."""
    assert file_path.stat().st_size > 0, f"Output file is empty: {file_path}"

    # Count rows (excluding header)
    with open(file_path, 'r') as f:
        row_count = sum(1 for _ in f) - 1

    assert row_count > 0, f"Output file has no data rows: {file_path}"
    logger.info(f"✓ File has {row_count} data rows")
    return row_count


def load_and_validate_clone_metrics() -> pd.DataFrame:
    """Load clone_metrics.csv and validate structure."""
    check_file_exists(CLONE_METRICS_PATH)

    df = pd.read_csv(CLONE_METRICS_PATH)

    # Required columns for clone density
    required_columns = ['file_path', 'clone_density']
    for col in required_columns:
        assert col in df.columns, f"Missing required column '{col}' in {CLONE_METRICS_PATH}"

    logger.info(f"✓ clone_metrics.csv has {len(df)} rows with columns: {list(df.columns)}")
    return df


def load_and_validate_perplexity_scores() -> pd.DataFrame:
    """Load perplexity_scores.csv and validate structure."""
    check_file_exists(PERPLEXITY_SCORES_PATH)

    df = pd.read_csv(PERPLEXITY_SCORES_PATH)

    # Required columns for perplexity
    required_columns = ['file_path', 'perplexity']
    for col in required_columns:
        assert col in df.columns, f"Missing required column '{col}' in {PERPLEXITY_SCORES_PATH}"

    logger.info(f"✓ perplexity_scores.csv has {len(df)} rows with columns: {list(df.columns)}")
    return df


def validate_clone_density_values(df: pd.DataFrame, column: str = 'clone_density') -> int:
    """
    Validate clone density values are valid.

    Valid clone density:
    - Not NaN
    - Not infinite
    - In range [0, 1]

    Returns count of valid rows.
    """
    values = df[column]

    # Check for NaN
    nan_count = values.isna().sum()
    assert nan_count == 0, f"Found {nan_count} NaN values in {column}"
    logger.info(f"✓ No NaN values in {column}")

    # Check for infinite values
    inf_count = np.isinf(values).sum()
    assert inf_count == 0, f"Found {inf_count} infinite values in {column}"
    logger.info(f"✓ No infinite values in {column}")

    # Check range [0, 1]
    invalid_range = ((values < 0) | (values > 1)).sum()
    assert invalid_range == 0, f"Found {invalid_range} values outside [0, 1] range in {column}"
    logger.info(f"✓ All {len(values)} values in {column} are in range [0, 1]")

    return len(df)


def validate_perplexity_values(df: pd.DataFrame, column: str = 'perplexity') -> int:
    """
    Validate perplexity values are valid.

    Valid perplexity:
    - Not NaN
    - Not infinite
    - Positive (> 0)

    Returns count of valid rows.
    """
    values = df[column]

    # Check for NaN
    nan_count = values.isna().sum()
    assert nan_count == 0, f"Found {nan_count} NaN values in {column}"
    logger.info(f"✓ No NaN values in {column}")

    # Check for infinite values
    inf_count = np.isinf(values).sum()
    assert inf_count == 0, f"Found {inf_count} infinite values in {column}"
    logger.info(f"✓ No infinite values in {column}")

    # Check positive values
    non_positive = (values <= 0).sum()
    assert non_positive == 0, f"Found {non_positive} non-positive values in {column}"
    logger.info(f"✓ All {len(values)} values in {column} are positive")

    return len(df)


def test_sc003_segment_count_minimum():
    """
    SC-003 Validation: At least 1000 code segments processed.

    This test verifies that the pipeline has successfully processed at least
    MIN_SEGMENTS_REQUIRED (1000) code segments with valid measurements.
    """
    logger.info("=" * 60)
    logger.info("SC-003 Segment Count Validation Test")
    logger.info("=" * 60)

    # Load and validate both output files
    clone_df = load_and_validate_clone_metrics()
    perplexity_df = load_and_validate_perplexity_scores()

    # Validate values in both files
    valid_clone_count = validate_clone_density_values(clone_df)
    valid_perplexity_count = validate_perplexity_values(perplexity_df)

    # Verify segment count meets minimum requirement
    assert valid_clone_count >= MIN_SEGMENTS_REQUIRED, (
        f"SC-003 FAILED: Only {valid_clone_count} valid segments found, "
        f"minimum required is {MIN_SEGMENTS_REQUIRED}"
    )
    logger.info(f"✓ Clone density: {valid_clone_count} valid segments >= {MIN_SEGMENTS_REQUIRED}")

    assert valid_perplexity_count >= MIN_SEGMENTS_REQUIRED, (
        f"SC-003 FAILED: Only {valid_perplexity_count} valid perplexity measurements found, "
        f"minimum required is {MIN_SEGMENTS_REQUIRED}"
    )
    logger.info(f"✓ Perplexity: {valid_perplexity_count} valid measurements >= {MIN_SEGMENTS_REQUIRED}")

    # Verify both files have same number of segments (joined correctly by T021)
    assert valid_clone_count == valid_perplexity_count, (
        f"Segment count mismatch: clone_metrics has {valid_clone_count}, "
        f"perplexity_scores has {valid_perplexity_count}"
    )
    logger.info(f"✓ Both files have matching segment count: {valid_clone_count}")

    logger.info("=" * 60)
    logger.info("SC-003 VALIDATION PASSED")
    logger.info(f"  - {valid_clone_count} segments with valid clone density")
    logger.info(f"  - {valid_perplexity_count} segments with valid perplexity")
    logger.info("=" * 60)


def test_sc003_segment_count_with_join():
    """
    SC-003 Validation: Verify joined metrics have at least 1000 valid segments.

    This test loads the joined output (if available) or validates that both
    files can be joined on file_path with at least 1000 matching records.
    """
    logger.info("=" * 60)
    logger.info("SC-003 Joined Metrics Validation Test")
    logger.info("=" * 60)

    clone_df = load_and_validate_clone_metrics()
    perplexity_df = load_and_validate_perplexity_scores()

    # Ensure file_path column exists in both for joining
    assert 'file_path' in clone_df.columns, "file_path column missing in clone_metrics"
    assert 'file_path' in perplexity_df.columns, "file_path column missing in perplexity_scores"

    # Join on file_path
    joined_df = pd.merge(
        clone_df[['file_path', 'clone_density']],
        perplexity_df[['file_path', 'perplexity']],
        on='file_path',
        how='inner'
    )

    logger.info(f"✓ Joined {len(clone_df)} clone records with {len(perplexity_df)} perplexity records")
    logger.info(f"  - Result: {len(joined_df)} matching segments")

    # Validate joined data has required columns
    assert 'clone_density' in joined_df.columns, "clone_density missing after join"
    assert 'perplexity' in joined_df.columns, "perplexity missing after join"

    # Validate values in joined data
    valid_clone = validate_clone_density_values(joined_df, 'clone_density')
    valid_perplexity = validate_perplexity_values(joined_df, 'perplexity')

    # Both validations should yield same count (same rows)
    assert valid_clone == valid_perplexity, "Mismatch in valid row counts after validation"

    # Check minimum threshold
    assert len(joined_df) >= MIN_SEGMENTS_REQUIRED, (
        f"SC-003 FAILED: Joined dataset has only {len(joined_df)} segments, "
        f"minimum required is {MIN_SEGMENTS_REQUIRED}"
    )

    logger.info("=" * 60)
    logger.info("SC-003 JOINED VALIDATION PASSED")
    logger.info(f"  - {len(joined_df)} segments with both clone density and perplexity")
    logger.info("=" * 60)


if __name__ == '__main__':
    """Run tests directly with pytest."""
    pytest.main([__file__, '-v', '--tb=short'])