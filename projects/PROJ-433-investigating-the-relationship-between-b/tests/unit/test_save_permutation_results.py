"""
Unit tests for T034: save_permutation_results.
"""
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Mock the analysis module functions to avoid dependency on full pipeline data
# We simulate the behavior of run_permutation_test
class MockAnalysis:
    @staticmethod
    def load_metrics_and_behavioral_data():
        # Return small synthetic arrays for testing logic only
        # These are NOT used for research results, only for verifying the save logic
        return (
            np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
            np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
            ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"]
        )

    @staticmethod
    def run_permutation_test(metrics, dsst, n_permutations, seed):
        # Simulate observed stat and null distribution
        np.random.seed(seed)
        observed = 0.85
        null_dist = np.random.normal(0.0, 0.2, n_permutations)
        p_val = np.mean(np.abs(null_dist) >= np.abs(observed))
        return observed, null_dist, p_val

def test_save_permutation_results_structure(monkeypatch):
    """
    Verify that the output TSV file is created and contains the expected structure.
    """
    # Patch the imports in the module under test
    import sys
    from unittest.mock import MagicMock

    # Create a mock for the analysis module
    mock_analysis = MagicMock()
    mock_analysis.load_metrics_and_behavioral_data = MockAnalysis.load_metrics_and_behavioral_data
    mock_analysis.run_permutation_test = MockAnalysis.run_permutation_test

    # Mock utils
    mock_utils = MagicMock()
    mock_utils.setup_logger = MagicMock(return_value=MagicMock())
    mock_utils.get_seeded_rng = MagicMock(return_value=np.random.default_rng(42))

    # Inject mocks
    sys.modules['analysis'] = mock_analysis
    sys.modules['utils'] = mock_utils

    # Import the function to test
    from save_permutation_results import save_permutation_results

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_permutation_results.tsv")
        
        # Run the function
        save_permutation_results(output_path=output_path, n_permutations=100, seed=42)

        # Verify file exists
        assert os.path.exists(output_path), "Output file was not created."

        # Load and check content
        df = pd.read_csv(output_path, sep="\t")

        # Check columns
        expected_cols = ["type", "value", "p_value", "n_permutations", "seed", "index"]
        assert all(col in df.columns for col in expected_cols), f"Missing columns. Found: {df.columns.tolist()}"

        # Check row counts
        # 1 observed + 100 null
        assert len(df) == 101, f"Expected 101 rows (1 observed + 100 null), got {len(df)}"

        # Check types
        observed_rows = df[df["type"] == "observed"]
        null_rows = df[df["type"] == "null"]

        assert len(observed_rows) == 1, "Expected exactly one 'observed' row."
        assert len(null_rows) == 100, "Expected exactly 100 'null' rows."

        # Check observed value is not NaN
        assert not pd.isna(observed_rows["value"].iloc[0]), "Observed value should not be NaN."
        
        # Check null values are not NaN
        assert not df["value"].isna().all(), "Null distribution values should not be all NaN."

        print("Test passed: Structure and content of permutation results TSV are correct.")

if __name__ == "__main__":
    test_save_permutation_results_structure()