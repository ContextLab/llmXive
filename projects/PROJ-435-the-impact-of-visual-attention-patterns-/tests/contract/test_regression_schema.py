"""
Contract test for regression output schema (T019).

This test verifies that the regression analysis script (code/05_regression_analysis.py)
produces an output file (data/derived/regression_results.csv) that strictly adheres to
the expected schema defined in the project specification.

It checks:
1. File existence.
2. Required columns are present (term, estimate, std_err, p_value, conf_int_lower, conf_int_upper).
3. Data types are appropriate for statistical inference.
4. The three-way interaction term is present if the model was run.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Expected output path based on tasks.md
OUTPUT_PATH = Path("data/derived/regression_results.csv")

REQUIRED_COLUMNS = [
    "term",
    "estimate",
    "std_err",
    "p_value",
    "conf_int_lower",
    "conf_int_upper"
]

INTERACTION_TERMS = [
    "fixation_duration:valence:cognitive_reflection_score"
]

@pytest.fixture(scope="module")
def regression_results():
    """
    Load the regression results file.
    Skips the test if the file does not exist (indicating the upstream task hasn't run yet).
    """
    if not OUTPUT_PATH.exists():
        pytest.skip(f"Output file {OUTPUT_PATH} not found. Upstream task (T024) may not have run.")
    
    df = pd.read_csv(OUTPUT_PATH)
    return df

class TestRegressionOutputSchema:
    """
    Contract tests for the regression results schema.
    """

    def test_file_exists(self):
        """Ensure the regression results file exists."""
        assert OUTPUT_PATH.exists(), f"Regression results file {OUTPUT_PATH} does not exist."

    def test_required_columns_present(self, regression_results):
        """
        Verify that all required statistical columns are present in the output.
        """
        missing_columns = set(REQUIRED_COLUMNS) - set(regression_results.columns)
        assert not missing_columns, (
            f"Missing required columns in regression output: {missing_columns}. "
            f"Expected: {REQUIRED_COLUMNS}, Found: {list(regression_results.columns)}"
        )

    def test_column_datatypes(self, regression_results):
        """
        Verify that numeric columns contain numeric data and 'term' is string/object.
        """
        # Check term is string-like
        assert regression_results["term"].dtype in ['object', 'string'], (
            f"Column 'term' must be string-like, found {regression_results['term'].dtype}"
        )

        # Check numeric columns
        numeric_cols = ["estimate", "std_err", "p_value", "conf_int_lower", "conf_int_upper"]
        for col in numeric_cols:
            if col in regression_results.columns:
                # Allow object if it contains mixed types, but ideally should be numeric
                # We check if they can be converted to numeric
                try:
                    pd.to_numeric(regression_results[col])
                except (ValueError, TypeError):
                    pytest.fail(f"Column '{col}' contains non-numeric data.")

    def test_interaction_term_present(self, regression_results):
        """
        Verify that the critical three-way interaction term is included in the results.
        This is a specific requirement of the study design (FR-004).
        """
        terms = regression_results["term"].astype(str).tolist()
        missing_interaction = [t for t in INTERACTION_TERMS if t not in terms]
        
        # Note: statsmodels might format the interaction term slightly differently (e.g. with brackets or dots)
        # We perform a loose check if the exact string isn't found, but the specific term name is expected.
        # For strict contract testing, we look for the specific component.
        found_interaction = False
        for term in terms:
            if "fixation_duration" in term and "valence" in term and "cognitive_reflection" in term:
                found_interaction = True
                break
        
        assert found_interaction, (
            f"The three-way interaction term (fixation x valence x CRT) is missing from the results. "
            f"Found terms: {terms}"
        )

    def test_no_null_values_in_critical_columns(self, regression_results):
        """
        Ensure that critical statistical columns do not contain null values.
        """
        critical_cols = ["estimate", "p_value"]
        for col in critical_cols:
            if col in regression_results.columns:
                assert not regression_results[col].isnull().any(), (
                    f"Column '{col}' contains null values. This indicates a failure in the regression estimation."
                )

    def test_p_value_range(self, regression_results):
        """
        Ensure p-values are within the valid range [0, 1].
        """
        if "p_value" in regression_results.columns:
            p_vals = pd.to_numeric(regression_results["p_value"])
            assert (p_vals >= 0).all() and (p_vals <= 1).all(), (
                f"P-values must be between 0 and 1. Found: {p_vals[p_vals < 0].tolist() + p_vals[p_vals > 1].tolist()}"
            )