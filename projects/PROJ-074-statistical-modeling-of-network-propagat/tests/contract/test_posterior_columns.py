"""Contract test ensuring posterior_summary.csv contains required columns.

This test verifies that the posterior_summary.csv output file contains all
required columns as specified in the data model and schema contracts:
- predictor: Name of the predictor variable
- mean: Posterior mean estimate
- sd: Posterior standard deviation
- lower_95: Lower bound of 95% credible interval
- upper_95: Upper bound of 95% credible interval
- prob_nonzero: Posterior probability of non-zero effect
- direction_consistent: Boolean indicating effect sign consistency across folds

Per Constitution Principle VII, this test logs validation results to pipeline.log.
"""

import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipeline.utils import setup_logger, set_global_seed

# Set global seed for reproducibility
set_global_seed(12345)

# Setup logger
logger = setup_logger("contract_test_posterior_columns")

# Required columns as per T024 specification
REQUIRED_COLUMNS = [
    "predictor",
    "mean",
    "sd",
    "lower_95",
    "upper_95",
    "prob_nonzero",
    "direction_consistent",
]

# Expected column order (predictor first, then statistics)
EXPECTED_COLUMN_ORDER = [
    "predictor",
    "mean",
    "sd",
    "lower_95",
    "upper_95",
    "prob_nonzero",
    "direction_consistent",
]

# Numeric columns that must have valid numeric values
NUMERIC_COLUMNS = ["mean", "sd", "lower_95", "upper_95", "prob_nonzero"]

# Boolean column
BOOLEAN_COLUMNS = ["direction_consistent"]

# Tolerance for floating-point comparisons
FLOAT_TOLERANCE = 1e-10

# Valid range for prob_nonzero (probability must be between 0 and 1)
PROB_MIN = 0.0
PROB_MAX = 1.0

# Valid range for direction_consistent (must be boolean-like)
BOOLEAN_VALUES = {True, False, "TRUE", "FALSE", "true", "false", 0, 1}


def load_posterior_summary(csv_path: str) -> pd.DataFrame:
    """Load and validate the posterior_summary.csv file.

    Args:
        csv_path: Path to the posterior_summary.csv file

    Returns:
        DataFrame containing the posterior summary data

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file cannot be parsed as CSV
    """
    path = Path(csv_path)
    if not path.exists():
        logger.error(f"posterior_summary.csv not found at: {csv_path}")
        raise FileNotFoundError(f"File not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded posterior_summary.csv with {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        raise ValueError(f"Failed to parse CSV: {e}")


def test_posterior_summary_file_exists(results_dir: str = "results"):
    """Test that posterior_summary.csv exists in the results directory.

    This is a prerequisite check before running column validation tests.
    """
    results_path = Path(results_dir)
    posterior_file = results_path / "posterior_summary.csv"

    if not posterior_file.exists():
        # Try alternative locations
        alt_paths = [
            Path("data/processed/posterior_summary.csv"),
            Path("output/posterior_summary.csv"),
        ]

        for alt_path in alt_paths:
            if alt_path.exists():
                logger.warning(f"Found posterior_summary.csv at alternative location: {alt_path}")
                return str(alt_path)

        pytest.fail(f"posterior_summary.csv not found in {results_dir}/ or alternative locations")

    logger.info(f"Found posterior_summary.csv at: {posterior_file}")
    return str(posterior_file)


def test_required_columns_present(df: pd.DataFrame):
    """Test that all required columns are present in the DataFrame.

    Per T024, the posterior_summary.csv must contain:
    - predictor, mean, sd, lower_95, upper_95, prob_nonzero, direction_consistent
    """
    df_columns = set(df.columns)
    required_set = set(REQUIRED_COLUMNS)

    missing = required_set - df_columns
    extra = df_columns - required_set

    if missing:
        logger.error(f"Missing required columns: {missing}")
        pytest.fail(f"Missing required columns: {missing}")

    if extra:
        logger.warning(f"Extra columns found (not required): {extra}")

    logger.info("All required columns are present")


def test_column_order_matches_spec(df: pd.DataFrame):
    """Test that columns appear in the expected order.

    While not strictly required for functionality, consistent column ordering
    aids in reproducibility and debugging.
    """
    actual_columns = list(df.columns)

    # Check that required columns appear in expected order
    expected_order = [col for col in EXPECTED_COLUMN_ORDER if col in actual_columns]
    actual_order = [col for col in actual_columns if col in EXPECTED_COLUMN_ORDER]

    if expected_order != actual_order:
        logger.warning(
            f"Column order differs from expected. "
            f"Expected: {expected_order}, Actual: {actual_order}"
        )
        # This is a warning, not a failure, as pandas doesn't enforce column order


def test_no_missing_values(df: pd.DataFrame):
    """Test that there are no missing values in required columns.

    Per T022, features.csv must contain all predictors with no missing values.
    This extends the same requirement to posterior_summary.csv.
    """
    for col in REQUIRED_COLUMNS:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            logger.error(f"Column '{col}' has {missing_count} missing values")
            pytest.fail(f"Column '{col}' has {missing_count} missing values")

    logger.info("No missing values found in required columns")


def test_numeric_columns_valid(df: pd.DataFrame):
    """Test that numeric columns contain valid numeric values.

    Verifies that mean, sd, lower_95, upper_95, and prob_nonzero
    can be converted to float and are within expected ranges.
    """
    for col in NUMERIC_COLUMNS:
        try:
            values = pd.to_numeric(df[col], errors="raise")
        except (ValueError, TypeError) as e:
            logger.error(f"Column '{col}' contains non-numeric values: {e}")
            pytest.fail(f"Column '{col}' contains non-numeric values")

        # Check for infinite values
        if values.isin([float("inf"), float("-inf")]).any():
            logger.error(f"Column '{col}' contains infinite values")
            pytest.fail(f"Column '{col}' contains infinite values")

    logger.info("All numeric columns contain valid numeric values")


def test_prob_nonzero_in_range(df: pd.DataFrame):
    """Test that prob_nonzero values are within valid probability range [0, 1].

    Per Bayesian inference requirements, posterior probability must be
    between 0 and 1 inclusive.
    """
    prob_values = pd.to_numeric(df["prob_nonzero"], errors="raise")

    if (prob_values < PROB_MIN).any():
        below_min = prob_values[prob_values < PROB_MIN].tolist()
        logger.error(f"prob_nonzero values below {PROB_MIN}: {below_min}")
        pytest.fail(f"prob_nonzero values below {PROB_MIN}")

    if (prob_values > PROB_MAX).any():
        above_max = prob_values[prob_values > PROB_MAX].tolist()
        logger.error(f"prob_nonzero values above {PROB_MAX}: {above_max}")
        pytest.fail(f"prob_nonzero values above {PROB_MAX}")

    logger.info("prob_nonzero values are within valid range [0, 1]")


def test_direction_consistent_boolean(df: pd.DataFrame):
    """Test that direction_consistent contains valid boolean-like values.

    The direction_consistent column should indicate whether the effect sign
    matches across folds (TRUE if consistent). Valid values include:
    - True/False (Python booleans)
    - "TRUE"/"FALSE" (uppercase strings)
    - "true"/"false" (lowercase strings)
    - 0/1 (numeric booleans)
    """
    for value in df["direction_consistent"].unique():
        if value not in BOOLEAN_VALUES:
            logger.error(f"Invalid boolean value in direction_consistent: {value}")
            pytest.fail(f"Invalid boolean value in direction_consistent: {value}")

    logger.info("direction_consistent contains valid boolean-like values")


def test_credible_interval_order(df: pd.DataFrame):
    """Test that lower_95 <= upper_95 for all rows.

    Credible intervals must have the lower bound less than or equal to
    the upper bound. This validates the statistical correctness of the
    posterior summary.
    """
    lower = pd.to_numeric(df["lower_95"], errors="raise")
    upper = pd.to_numeric(df["upper_95"], errors="raise")

    invalid_mask = lower > upper
    if invalid_mask.any():
        invalid_indices = df[invalid_mask].index.tolist()
        logger.error(f"Rows with lower_95 > upper_95: {invalid_indices}")
        pytest.fail(f"Found {invalid_mask.sum()} rows with invalid credible intervals")

    logger.info("All credible intervals have valid lower <= upper ordering")


def test_standard_deviation_non_negative(df: pd.DataFrame):
    """Test that standard deviation (sd) is non-negative.

    Standard deviation is a measure of dispersion and must be >= 0.
    """
    sd_values = pd.to_numeric(df["sd"], errors="raise")

    if (sd_values < 0).any():
        negative_sd = sd_values[sd_values < 0].tolist()
        logger.error(f"Negative standard deviation values found: {negative_sd}")
        pytest.fail("Negative standard deviation values found")

    logger.info("All standard deviation values are non-negative")


def test_predictor_column_non_empty(df: pd.DataFrame):
    """Test that predictor column contains non-empty strings.

    The predictor column identifies the variable name for each posterior
    estimate and must not be empty.
    """
    empty_mask = df["predictor"].isna() | (df["predictor"].astype(str).str.strip() == "")
    if empty_mask.any():
        empty_indices = df[empty_mask].index.tolist()
        logger.error(f"Empty predictor values at indices: {empty_indices}")
        pytest.fail(f"Found {empty_mask.sum()} empty predictor values")

    logger.info("All predictor values are non-empty")


def test_at_least_one_row(df: pd.DataFrame):
    """Test that the posterior summary contains at least one row.

    A valid posterior summary must contain at least one predictor estimate.
    """
    if len(df) == 0:
        logger.error("posterior_summary.csv is empty (0 rows)")
        pytest.fail("posterior_summary.csv is empty")

    logger.info(f"posterior_summary.csv contains {len(df)} predictor estimates")


def test_95_percent_interval_width(df: pd.DataFrame):
    """Test that 95% credible intervals have reasonable width.

    Very narrow intervals (width < 1e-10) may indicate numerical issues.
    Very wide intervals relative to the mean may indicate convergence issues.
    """
    lower = pd.to_numeric(df["lower_95"], errors="raise")
    upper = pd.to_numeric(df["upper_95"], errors="raise")
    width = upper - lower

    # Check for extremely narrow intervals
    extremely_narrow = width < FLOAT_TOLERANCE
    if extremely_narrow.any():
        narrow_indices = df[extremely_narrow].index.tolist()
        logger.warning(
            f"Found {extremely_narrow.sum()} extremely narrow intervals "
            f"(width < {FLOAT_TOLERANCE}): {narrow_indices}"
        )

    logger.info("Credible interval widths checked")


def test_column_types_match_schema(df: pd.DataFrame):
    """Test that column data types match the expected schema.

    Verifies that:
    - predictor is string/object
    - mean, sd, lower_95, upper_95, prob_nonzero are numeric
    - direction_consistent is boolean-like
    """
    # Check predictor is string-like
    if not pd.api.types.is_string_dtype(df["predictor"]) and not df["predictor"].apply(lambda x: isinstance(x, str)).all():
        logger.warning("predictor column is not string type")

    # Check numeric columns
    for col in NUMERIC_COLUMNS:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                pd.to_numeric(df[col], errors="raise")
            except (ValueError, TypeError):
                logger.error(f"Column '{col}' is not numeric and cannot be converted")
                pytest.fail(f"Column '{col}' is not numeric")

    logger.info("Column types match expected schema")


# Main pytest test function that runs all validations
@pytest.fixture
def posterior_df():
    """Load the posterior_summary.csv file for testing."""
    csv_path = test_posterior_summary_file_exists()
    return load_posterior_summary(csv_path)

@pytest.mark.contract
def test_posterior_summary_columns(posterior_df):
    """Main contract test for posterior_summary.csv columns.

    This test aggregates all column validation checks into a single
    pytest test function that will pass only if all validations succeed.
    """
    logger.info("Running posterior_summary.csv column contract test")

    # Run all validation checks
    test_required_columns_present(posterior_df)
    test_column_order_matches_spec(posterior_df)
    test_no_missing_values(posterior_df)
    test_numeric_columns_valid(posterior_df)
    test_prob_nonzero_in_range(posterior_df)
    test_direction_consistent_boolean(posterior_df)
    test_credible_interval_order(posterior_df)
    test_standard_deviation_non_negative(posterior_df)
    test_predictor_column_non_empty(posterior_df)
    test_at_least_one_row(posterior_df)
    test_95_percent_interval_width(posterior_df)
    test_column_types_match_schema(posterior_df)

    logger.info("All posterior_summary.csv column validations passed")