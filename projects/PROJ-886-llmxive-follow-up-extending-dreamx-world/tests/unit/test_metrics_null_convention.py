import os
import csv
import tempfile
import pytest
from pathlib import Path

from analysis.metrics_writer import write_metrics_csv, load_metrics_csv, NULL_VALUE_SENTINEL

class TestMetricsNullConvention:
    """
    Tests for T027b: Reconciliation of Spec FR-004 'sentinel value' requirement
    with Plan 'null' convention.
    """

    def test_null_values_written_as_empty_strings(self):
        """Verify that None values are written as empty strings in CSV."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            metrics = [
                {
                    "trajectory_id": "traj_001",
                    "model": "dreamx_lite",
                    "mae_position": 0.123,
                    "mae_rotation": 0.045,
                    "convergence": True,
                    "sfm_failure_reason": "",
                    "scale_drift": 1.02
                },
                {
                    "trajectory_id": "traj_002",
                    "model": "dreamx_lite",
                    "mae_position": None,
                    "mae_rotation": None,
                    "convergence": False,
                    "sfm_failure_reason": "insufficient_features",
                    "scale_drift": None
                }
            ]

            write_metrics_csv(metrics, temp_path, log_exception=False)

            # Read raw CSV to verify empty strings
            with open(temp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Check that null values are empty strings
            assert rows[1]["mae_position"] == ""
            assert rows[1]["mae_rotation"] == ""
            assert rows[1]["scale_drift"] == ""
            assert rows[1]["sfm_failure_reason"] == "insufficient_features"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_empty_strings_loaded_as_none(self):
        """Verify that empty strings are loaded back as None."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            # Write raw CSV with empty strings
            with open(temp_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=[
                    "trajectory_id", "model", "mae_position", "mae_rotation",
                    "convergence", "sfm_failure_reason", "scale_drift"
                ])
                writer.writeheader()
                writer.writerow({
                    "trajectory_id": "traj_001",
                    "model": "dreamx_lite",
                    "mae_position": "",
                    "mae_rotation": "",
                    "convergence": "False",
                    "sfm_failure_reason": "optimization_divergence",
                    "scale_drift": ""
                })

            # Load using our function
            loaded = load_metrics_csv(temp_path)

            assert len(loaded) == 1
            assert loaded[0]["mae_position"] is None
            assert loaded[0]["mae_rotation"] is None
            assert loaded[0]["scale_drift"] is None
            assert loaded[0]["convergence"] is False
            assert loaded[0]["sfm_failure_reason"] == "optimization_divergence"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_roundtrip_preserves_null_values(self):
        """Verify that write -> load roundtrip preserves None values."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            original_metrics = [
                {
                    "trajectory_id": "traj_001",
                    "model": "dreamx_lite",
                    "mae_position": 0.123,
                    "mae_rotation": 0.045,
                    "convergence": True,
                    "sfm_failure_reason": "",
                    "scale_drift": 1.02
                },
                {
                    "trajectory_id": "traj_002",
                    "model": "dreamx_lite",
                    "mae_position": None,
                    "mae_rotation": None,
                    "convergence": False,
                    "sfm_failure_reason": "insufficient_features",
                    "scale_drift": None
                }
            ]

            write_metrics_csv(original_metrics, temp_path, log_exception=False)
            loaded_metrics = load_metrics_csv(temp_path)

            # Verify roundtrip
            assert len(loaded_metrics) == len(original_metrics)
            for orig, loaded in zip(original_metrics, loaded_metrics):
                assert orig["trajectory_id"] == loaded["trajectory_id"]
                assert orig["model"] == loaded["model"]
                assert orig["convergence"] == loaded["convergence"]
                assert orig["sfm_failure_reason"] == loaded["sfm_failure_reason"]

                # Check null handling
                if orig["mae_position"] is None:
                    assert loaded["mae_position"] is None
                else:
                    assert abs(orig["mae_position"] - loaded["mae_position"]) < 1e-6

                if orig["mae_rotation"] is None:
                    assert loaded["mae_rotation"] is None
                else:
                    assert abs(orig["mae_rotation"] - loaded["mae_rotation"]) < 1e-6

                if orig["scale_drift"] is None:
                    assert loaded["scale_drift"] is None
                else:
                    assert abs(orig["scale_drift"] - loaded["scale_drift"]) < 1e-6

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_statistical_filtering_with_nulls(self):
        """
        Verify that null values allow proper filtering for statistical tests.
        This is the key requirement for statistical validity.
        """
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            metrics = [
                {
                    "trajectory_id": "traj_001",
                    "model": "dreamx_lite",
                    "mae_position": 0.123,
                    "mae_rotation": 0.045,
                    "convergence": True,
                    "sfm_failure_reason": "",
                    "scale_drift": 1.02
                },
                {
                    "trajectory_id": "traj_002",
                    "model": "dreamx_lite",
                    "mae_position": None,
                    "mae_rotation": None,
                    "convergence": False,
                    "sfm_failure_reason": "insufficient_features",
                    "scale_drift": None
                },
                {
                    "trajectory_id": "traj_003",
                    "model": "dreamx_lite",
                    "mae_position": 0.089,
                    "mae_rotation": 0.032,
                    "convergence": True,
                    "sfm_failure_reason": "",
                    "scale_drift": 0.98
                }
            ]

            write_metrics_csv(metrics, temp_path, log_exception=False)
            loaded = load_metrics_csv(temp_path)

            # Filter for converged trajectories (as done in Wilcoxon test)
            converged = [m for m in loaded if m["convergence"]]

            assert len(converged) == 2
            assert all(m["mae_position"] is not None for m in converged)
            assert all(m["mae_rotation"] is not None for m in converged)
            assert all(m["scale_drift"] is not None for m in converged)

            # Failed trajectories should have null values
            failed = [m for m in loaded if not m["convergence"]]
            assert len(failed) == 1
            assert failed[0]["mae_position"] is None
            assert failed[0]["mae_rotation"] is None
            assert failed[0]["scale_drift"] is None

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_exception_logging(self, caplog):
        """Verify that the reconciliation exception is logged."""
        import logging

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            temp_path = f.name

        try:
            metrics = [
                {
                    "trajectory_id": "traj_001",
                    "model": "dreamx_lite",
                    "mae_position": 0.123,
                    "mae_rotation": 0.045,
                    "convergence": True,
                    "sfm_failure_reason": "",
                    "scale_drift": 1.02
                }
            ]

            with caplog.at_level(logging.INFO):
                write_metrics_csv(metrics, temp_path, log_exception=True)

            # Check that the reconciliation message was logged
            assert any(
                "Reconciling Spec FR-004 'sentinel value' with Plan 'null' convention" in record.message
                for record in caplog.records
            )

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)