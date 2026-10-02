import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function to test
# Assuming run_sensitivity_analysis is in code/analysis.py
# We need to ensure the import path is correct relative to the test runner
# For this test file, we assume it's run from the project root or code is in sys.path
try:
    from analysis import run_sensitivity_analysis
except ImportError:
    # Fallback if running directly in a specific environment
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))
    from analysis import run_sensitivity_analysis


class TestSensitivitySweep:
    """
    Unit tests for the sensitivity analysis sweep functionality.
    """

    def test_sensitivity_sweep_generates_valid_range(self):
        """
        Asserts that the output covers the full threshold range from 0.0 to 1.0.
        """
        # Create a mock dataset with binary predictions and true labels
        # We simulate a scenario where we have probabilities and ground truth
        np.random.seed(42)
        n_samples = 100
        
        # Mock true labels (0 or 1)
        y_true = np.random.randint(0, 2, n_samples)
        # Mock predicted probabilities (0.0 to 1.0)
        y_proba = np.random.rand(n_samples)

        # Define a temporary output directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_csv = Path(tmp_dir) / "sweep_results.csv"
            output_fpr_fnr = Path(tmp_dir) / "sensitivity_fpr_fnr.csv"
            output_fig = Path(tmp_dir) / "sensitivity_curve.png"

            # Run the analysis
            # Note: The actual function signature might vary, adjust as needed based on analysis.py
            # Assuming it takes y_true, y_proba, and output paths
            try:
                run_sensitivity_analysis(
                    y_true=y_true,
                    y_proba=y_proba,
                    output_csv=str(output_csv),
                    output_fpr_fnr=str(output_fpr_fnr),
                    output_fig=str(output_fig)
                )
            except Exception as e:
                # If the function fails due to missing dependencies or other issues,
                # we might need to mock more or adjust the test.
                # However, the goal is to verify the RANGE logic.
                # If the function is not fully implemented in the environment, 
                # we assert the existence of the logic in the source code or 
                # rely on the fact that the task implementation must produce this.
                # For this test to pass in a real run, the function must exist and work.
                pytest.fail(f"run_sensitivity_analysis failed to execute: {e}")

            # Load the results
            assert output_csv.exists(), "Sweep results CSV was not created."
            df = pd.read_csv(output_csv)

            # Check that the threshold column exists
            assert 'threshold' in df.columns, "Threshold column missing in results."

            # Check the range
            thresholds = df['threshold'].values
            min_thresh = thresholds.min()
            max_thresh = thresholds.max()

            # The sweep should cover 0.0 to 1.0 (or very close to it)
            # Based on task T028, it uses np.arange(0.0, 1.0, 0.01)
            # So we expect min ~ 0.0 and max ~ 0.99 (or 1.0 if inclusive)
            assert min_thresh <= 0.01, f"Min threshold {min_thresh} is too high."
            assert max_thresh >= 0.99, f"Max threshold {max_thresh} is too low."

            # Check that FPR and FNR columns exist (Task T028 requirement)
            assert 'fpr' in df.columns, "FPR column missing."
            assert 'fnr' in df.columns, "FNR column missing."

    def test_sensitivity_sweep_includes_fpr_fnr(self):
        """
        Asserts that the output explicitly includes FPR and FNR for each step.
        """
        # Similar setup as above
        np.random.seed(42)
        n_samples = 100
        y_true = np.random.randint(0, 2, n_samples)
        y_proba = np.random.rand(n_samples)

        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_csv = Path(tmp_dir) / "sweep_results.csv"
            output_fpr_fnr = Path(tmp_dir) / "sensitivity_fpr_fnr.csv"
            output_fig = Path(tmp_dir) / "sensitivity_curve.png"

            try:
                run_sensitivity_analysis(
                    y_true=y_true,
                    y_proba=y_proba,
                    output_csv=str(output_csv),
                    output_fpr_fnr=str(output_fpr_fnr),
                    output_fig=str(output_fig)
                )
            except Exception as e:
                pytest.fail(f"run_sensitivity_analysis failed: {e}")

            df = pd.read_csv(output_csv)

            # Verify columns
            required_cols = ['threshold', 'accuracy', 'precision', 'recall', 'f1', 'fpr', 'fnr']
            for col in required_cols:
                assert col in df.columns, f"Required column '{col}' missing."

            # Verify no nulls in FPR/FNR
            assert not df['fpr'].isnull().any(), "FPR contains null values."
            assert not df['fnr'].isnull().any(), "FNR contains null values."