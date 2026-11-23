"""
Integration tests for overfitting detection logic.
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from code.services.overfitting_detector import (
    calculate_overfitting_metrics,
    detect_overfitting,
    load_cv_results,
    save_overfitting_report,
)


class TestOverfittingDetector:
    """Test suite for overfitting detection functions."""

    @pytest.fixture
    def mock_cv_results(self):
        """Create mock cross-validation results with overfitting and non-overfitting cases."""
        return {
            "systems": [
                {
                    "system_name": "Fe-Cr-Mo",
                    "folds": [
                        {
                            "fold_id": 1,
                            "train_score": 0.95,
                            "val_score": 0.70,
                        },
                        {
                            "fold_id": 2,
                            "train_score": 0.94,
                            "val_score": 0.68,
                        },
                        {
                            "fold_id": 3,
                            "train_score": 0.96,
                            "val_score": 0.72,
                        },
                    ],
                },
                {
                    "system_name": "Fe-Cr-V",
                    "folds": [
                        {
                            "fold_id": 1,
                            "train_score": 0.85,
                            "val_score": 0.82,
                        },
                        {
                            "fold_id": 2,
                            "train_score": 0.86,
                            "val_score": 0.83,
                        },
                        {
                            "fold_id": 3,
                            "train_score": 0.84,
                            "val_score": 0.81,
                        },
                    ],
                },
                {
                    "system_name": "Fe-Mo-W",
                    "folds": [
                        {
                            "fold_id": 1,
                            "train_score": 0.98,
                            "val_score": 0.50,
                        },
                        {
                            "fold_id": 2,
                            "train_score": 0.97,
                            "val_score": 0.48,
                        },
                        {
                            "fold_id": 3,
                            "train_score": 0.99,
                            "val_score": 0.52,
                        },
                    ],
                },
            ]
        }

    @pytest.fixture
    def temp_cv_file(self, mock_cv_results):
        """Create a temporary CV results file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(mock_cv_results, f)
            temp_path = Path(f.name)
        yield temp_path
        temp_path.unlink()

    def test_calculate_overfitting_metrics(self, mock_cv_results):
        """Test calculation of overfitting metrics."""
        metrics = calculate_overfitting_metrics(mock_cv_results)

        assert len(metrics) == 3

        # Check Fe-Cr-Mo (moderate overfitting)
        fe_cr_mo = next(m for m in metrics if m["system_name"] == "Fe-Cr-Mo")
        assert fe_cr_mo["mean_train_score"] == pytest.approx(0.95, rel=0.01)
        assert fe_cr_mo["mean_val_score"] == pytest.approx(0.70, rel=0.01)
        assert fe_cr_mo["overfitting_gap"] == pytest.approx(0.25, rel=0.01)

        # Check Fe-Cr-V (no overfitting)
        fe_cr_v = next(m for m in metrics if m["system_name"] == "Fe-Cr-V")
        assert fe_cr_v["overfitting_gap"] == pytest.approx(0.03, rel=0.01)

        # Check Fe-Mo-W (severe overfitting)
        fe_mo_w = next(m for m in metrics if m["system_name"] == "Fe-Mo-W")
        assert fe_mo_w["overfitting_gap"] == pytest.approx(0.47, rel=0.01)

    def test_detect_overfitting(self, mock_cv_results):
        """Test overfitting detection with default thresholds."""
        metrics = calculate_overfitting_metrics(mock_cv_results)
        flagged = detect_overfitting(metrics, gap_threshold=0.15, ratio_threshold=0.2)

        assert len(flagged) == 3

        # Fe-Cr-Mo should be flagged (gap=0.25 > 0.15, ratio > 0.2)
        fe_cr_mo = next(f for f in flagged if f["system_name"] == "Fe-Cr-Mo")
        assert fe_cr_mo["status"] == "OVERFITTING_DETECTED"
        assert len(fe_cr_mo["flag_reason"]) > 0

        # Fe-Cr-V should NOT be flagged (gap=0.03 < 0.15)
        fe_cr_v = next(f for f in flagged if f["system_name"] == "Fe-Cr-V")
        assert fe_cr_v["status"] == "OK"
        assert len(fe_cr_v["flag_reason"]) == 0

        # Fe-Mo-W should be flagged (severe overfitting)
        fe_mo_w = next(f for f in flagged if f["system_name"] == "Fe-Mo-W")
        assert fe_mo_w["status"] == "OVERFITTING_DETECTED"
        assert len(fe_mo_w["flag_reason"]) > 0

    def test_detect_overfitting_with_custom_thresholds(self, mock_cv_results):
        """Test overfitting detection with stricter thresholds."""
        metrics = calculate_overfitting_metrics(mock_cv_results)
        # Stricter: gap > 0.3 and ratio > 0.5
        flagged = detect_overfitting(metrics, gap_threshold=0.3, ratio_threshold=0.5)

        # Only Fe-Mo-W should be flagged with stricter thresholds
        overfitting_count = sum(
            1 for f in flagged if f["status"] == "OVERFITTING_DETECTED"
        )
        assert overfitting_count == 1
        assert flagged[2]["status"] == "OVERFITTING_DETECTED"

    def test_save_overfitting_report(self, mock_cv_results, temp_cv_file):
        """Test saving overfitting report to file."""
        metrics = calculate_overfitting_metrics(mock_cv_results)
        flagged = detect_overfitting(metrics)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_overfitting_report.json"
            result_path = save_overfitting_report(flagged, output_path)

            assert result_path.exists()
            with open(result_path, "r") as f:
                report = json.load(f)

            assert report["total_systems"] == 3
            assert report["overfitting_detected_count"] == 2
            assert len(report["systems"]) == 3

    def test_load_cv_results_file_not_found(self):
        """Test loading CV results when file does not exist."""
        with pytest.raises(FileNotFoundError):
            load_cv_results()

    def test_empty_folds_handling(self):
        """Test handling of systems with empty folds."""
        mock_results = {
            "systems": [
                {
                    "system_name": "Empty-System",
                    "folds": [],
                }
            ]
        }

        metrics = calculate_overfitting_metrics(mock_results)
        # Should skip empty systems
        assert len(metrics) == 0

    def test_insufficient_scores_handling(self):
        """Test handling of systems with missing scores."""
        mock_results = {
            "systems": [
                {
                    "system_name": "Incomplete-System",
                    "folds": [
                        {"fold_id": 1, "train_score": 0.9, "val_score": None},
                        {"fold_id": 2, "train_score": 0.85, "val_score": None},
                    ],
                }
            ]
        }

        metrics = calculate_overfitting_metrics(mock_results)
        # Should skip systems without validation scores
        assert len(metrics) == 0