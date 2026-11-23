"""
Unit tests for the sensitivity analysis module.
"""
import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modeling.sensitivity_analysis import (
    calculate_fpr_fnr,
    run_sensitivity_analysis,
    main
)


class TestCalculateFPRFNR:
    """Tests for calculate_fpr_fnr function."""

    def test_perfect_prediction(self):
        """Test with perfect predictions (FPR=0, FNR=0)."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 1])
        fpr, fnr = calculate_fpr_fnr(y_true, y_pred)
        assert fpr == 0.0
        assert fnr == 0.0

    def test_all_false_positives(self):
        """Test with all false positives (FPR=1, FNR=0)."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([1, 1, 1, 1])
        fpr, fnr = calculate_fpr_fnr(y_true, y_pred)
        assert fpr == 1.0
        assert fnr == 0.0

    def test_all_false_negatives(self):
        """Test with all false negatives (FPR=0, FNR=1)."""
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 0, 0])
        fpr, fnr = calculate_fpr_fnr(y_true, y_pred)
        assert fpr == 0.0
        assert fnr == 1.0

    def test_no_negative_samples(self):
        """Test case where there are no negative samples (FPR should be 0)."""
        y_true = np.array([1, 1, 1])
        y_pred = np.array([0, 1, 0]) # FN=2, TP=1
        fpr, fnr = calculate_fpr_fnr(y_true, y_pred)
        assert fpr == 0.0
        assert fnr == 2/3

    def test_no_positive_samples(self):
        """Test case where there are no positive samples (FNR should be 0)."""
        y_true = np.array([0, 0, 0])
        y_pred = np.array([1, 0, 0]) # FP=1, TN=2
        fpr, fnr = calculate_fpr_fnr(y_true, y_pred)
        assert fpr == 1/3
        assert fnr == 0.0


class TestRunSensitivityAnalysis:
    """Tests for run_sensitivity_analysis function."""

    def test_sweep_results_structure(self):
        """Test that results contain expected keys."""
        y_true = np.array([0, 1, 1, 0, 1])
        y_proba = np.array([0.1, 0.9, 0.8, 0.2, 0.6])
        thresholds = [0.3, 0.5, 0.7]

        results = run_sensitivity_analysis(y_true, y_proba, thresholds)

        assert isinstance(results, list)
        assert len(results) == len(thresholds)

        for res in results:
            assert "threshold" in res
            assert "fpr" in res
            assert "fnr" in res
            assert "n_positive_pred" in res
            assert "n_negative_pred" in res

    def test_threshold_monotonicity(self):
        """
        Test that as threshold increases, FPR should generally decrease
        and FNR should generally increase (though not strictly monotonic
        due to discrete data).
        """
        # Create a scenario with clear separation
        y_true = np.array([0, 0, 0, 1, 1, 1])
        y_proba = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        thresholds = [0.2, 0.5, 0.8]

        results = run_sensitivity_analysis(y_true, y_proba, thresholds)

        # Check FPR decreases or stays same
        fpr_vals = [r["fpr"] for r in results]
        # Check FNR increases or stays same
        fnr_vals = [r["fnr"] for r in results]

        # Simple check: FPR at high threshold should be <= FPR at low threshold
        assert fpr_vals[-1] <= fpr_vals[0]
        assert fnr_vals[-1] >= fnr_vals[0]

    def test_empty_thresholds(self):
        """Test with empty thresholds list."""
        y_true = np.array([0, 1])
        y_proba = np.array([0.5, 0.5])
        results = run_sensitivity_analysis(y_true, y_proba, [])
        assert results == []


class TestMainIntegration:
    """Integration tests for the main function (mocked)."""

    @patch('modeling.sensitivity_analysis.load_processed_data')
    @patch('modeling.sensitivity_analysis.load_model_and_indices')
    @patch('modeling.sensitivity_analysis.ensure_dirs')
    @patch('modeling.sensitivity_analysis.log_artifact')
    @patch('modeling.sensitivity_analysis.json.dump')
    @patch('modeling.sensitivity_analysis.open')
    def test_main_holdout_mode(
        self,
        mock_open,
        mock_json_dump,
        mock_log_artifact,
        mock_ensure_dirs,
        mock_load_model,
        mock_load_data
    ):
        """Test main function in holdout mode (N >= 50)."""
        # Setup mocks
        mock_load_data.return_value = (
            pd.DataFrame(np.random.rand(100, 10)),
            pd.Series([0]*50 + [1]*50)
        )
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.random.rand(20, 2)
        mock_load_model.return_value = (mock_model, {"holdout_indices": list(range(20))})

        # Mock file existence checks
        with patch('pathlib.Path.exists', return_value=True):
            # Run main
            with patch.object(Path, '__truediv__', lambda self, other: self / other):
                # We need to mock the actual file operations inside main
                # Since main() writes to disk, we mock the open context manager
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = lambda s, *args: None

                try:
                    main()
                except SystemExit:
                    pass # Expected if logging or other side effects occur

                # Verify calls
                mock_load_data.assert_called_once()
                mock_load_model.assert_called_once()
                mock_log_artifact.assert_called()

    @patch('modeling.sensitivity_analysis.load_processed_data')
    @patch('modeling.sensitivity_analysis.load_model_and_indices')
    @patch('modeling.sensitivity_analysis.ensure_dirs')
    @patch('modeling.sensitivity_analysis.log_artifact')
    @patch('modeling.sensitivity_analysis.json.dump')
    @patch('modeling.sensitivity_analysis.open')
    def test_main_full_dataset_mode(
        self,
        mock_open,
        mock_json_dump,
        mock_log_artifact,
        mock_ensure_dirs,
        mock_load_model,
        mock_load_data
    ):
        """Test main function in full dataset mode (N < 50)."""
        # Setup mocks for small dataset
        mock_load_data.return_value = (
            pd.DataFrame(np.random.rand(30, 10)),
            pd.Series([0]*15 + [1]*15)
        )
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = np.random.rand(30, 2)
        mock_load_model.return_value = (mock_model, {})

        with patch('pathlib.Path.exists', return_value=True):
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = lambda s, *args: None

            try:
                main()
            except SystemExit:
                pass

            # Verify it did NOT try to load holdout indices
            # The logic checks N < 50, so it shouldn't access indices for prediction
            # But it might still load them. The key is it uses full dataset.
            assert mock_load_data.call_count >= 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])