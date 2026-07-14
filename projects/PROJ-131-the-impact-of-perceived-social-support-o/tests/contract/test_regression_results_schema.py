"""
Contract test for regression results schema.

This test verifies that the regression results saved to
`data/results/regression_results.csv` adhere to the expected schema
defined by the research pipeline requirements for User Story 2.

Expected columns:
- outcome: str (Depression, Anxiety, or PTSD)
- predictor: str (e.g., 'social_support', 'harassment_exposure', 'interaction')
- coef: float (coefficient estimate)
- std_err: float (standard error, HC3 if robust)
- p_value: float (raw p-value)
- p_adj: float (Benjamini-Hochberg adjusted p-value)
- ci_lower: float (lower bound of BCa bootstrap CI)
- ci_upper: float (upper bound of BCa bootstrap CI)
- n_obs: int (number of observations used)
- r_squared: float (model R-squared)
"""

import os
import pandas as pd
import pytest
from pathlib import Path

# Constants
RESULTS_PATH = Path("data/results/regression_results.csv")

REQUIRED_COLUMNS = [
    "outcome",
    "predictor",
    "coef",
    "std_err",
    "p_value",
    "p_adj",
    "ci_lower",
    "ci_upper",
    "n_obs",
    "r_squared",
]

VALID_OUTCOMES = ["Depression", "Anxiety", "PTSD"]

# Optional: Define expected data types if strict typing is required
EXPECTED_DTYPES = {
    "outcome": "object",
    "predictor": "object",
    "coef": "float64",
    "std_err": "float64",
    "p_value": "float64",
    "p_adj": "float64",
    "ci_lower": "float64",
    "ci_upper": "float64",
    "n_obs": "int64",
    "r_squared": "float64",
}


@pytest.fixture(scope="module")
def results_df():
    """Load the regression results file if it exists."""
    if not RESULTS_PATH.exists():
        pytest.skip(
            f"Results file not found at {RESULTS_PATH}. "
            "Run the analysis pipeline (T020-T024) before running this contract test."
        )
    return pd.read_csv(RESULTS_PATH)


class TestRegressionResultsSchema:
    """Contract tests for the regression results dataframe structure."""

    def test_file_exists(self):
        """Verify the output file exists."""
        assert RESULTS_PATH.exists(), f"File {RESULTS_PATH} does not exist."

    def test_required_columns_present(self, results_df: pd.DataFrame):
        """Verify all required columns are present."""
        missing = set(REQUIRED_COLUMNS) - set(results_df.columns)
        assert not missing, f"Missing required columns: {missing}"

    def test_column_order(self, results_df: pd.DataFrame):
        """Verify columns are in the expected order (optional but good practice)."""
        # We check that the dataframe columns start with the required ones in order
        # or simply that the required set matches the dataframe columns exactly.
        # Here we enforce exact match for strictness.
        assert list(results_df.columns) == REQUIRED_COLUMNS, (
            f"Column order mismatch. Expected {REQUIRED_COLUMNS}, "
            f"got {list(results_df.columns)}"
        )

    def test_valid_outcomes(self, results_df: pd.DataFrame):
        """Verify all outcome values are from the allowed list."""
        invalid_outcomes = set(results_df["outcome"].unique()) - set(VALID_OUTCOMES)
        assert not invalid_outcomes, (
            f"Invalid outcome values found: {invalid_outcomes}. "
            f"Allowed: {VALID_OUTCOMES}"
        )

    def test_no_missing_values(self, results_df: pd.DataFrame):
        """Verify there are no NaN values in the results."""
        null_counts = results_df.isnull().sum()
        total_nulls = null_counts.sum()
        assert total_nulls == 0, f"Found {total_nulls} missing values in results."

    def test_positive_std_err(self, results_df: pd.DataFrame):
        """Verify standard errors are non-negative."""
        assert (results_df["std_err"] >= 0).all(), "Standard errors must be >= 0."

    def test_ci_bounds_logical(self, results_df: pd.DataFrame):
        """Verify CI lower bound is <= CI upper bound."""
        assert (results_df["ci_lower"] <= results_df["ci_upper"]).all(), (
            "CI lower bound must be <= CI upper bound."
        )

    def test_n_obs_positive(self, results_df: pd.DataFrame):
        """Verify number of observations is positive."""
        assert (results_df["n_obs"] > 0).all(), "Number of observations must be > 0."

    def test_r_squared_range(self, results_df: pd.DataFrame):
        """Verify R-squared is within [0, 1]."""
        assert (results_df["r_squared"] >= 0).all() and (
            results_df["r_squared"] <= 1
        ).all(), "R-squared must be between 0 and 1."

    def test_p_value_range(self, results_df: pd.DataFrame):
        """Verify p-values are within [0, 1]."""
        assert (results_df["p_value"] >= 0).all() and (
            results_df["p_value"] <= 1
        ).all(), "Raw p-values must be between 0 and 1."

    def test_p_adj_range(self, results_df: pd.DataFrame):
        """Verify adjusted p-values are within [0, 1]."""
        assert (results_df["p_adj"] >= 0).all() and (
            results_df["p_adj"] <= 1
        ).all(), "Adjusted p-values must be between 0 and 1."