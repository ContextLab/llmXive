import json
import tempfile
from pathlib import Path
import pytest

from model.eval_runner import run_success_criteria_assertion, SURROGATE_DISCLAIMER


class TestEvalRunnerDisclaimer:
    """Tests for T022a: Surrogate model disclaimer injection."""

    def test_add_disclaimer_to_training_logs(self):
        """Verify disclaimer is added to training_logs.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            logs_path = tmp_path / "training_logs.json"

            # Create a mock training log without metadata
            mock_data = {
                "epoch": 10,
                "loss": 0.05,
                "metrics": {"mape": 5.2, "rmse": 0.12},
                "memory_peak": 2.1
            }
            with open(logs_path, 'w') as f:
                json.dump(mock_data, f)

            # Run the assertion
            run_success_criteria_assertion(
                training_logs_path=logs_path,
                generalization_metrics_path=tmp_path / "nonexistent.json"
            )

            # Verify update
            with open(logs_path, 'r') as f:
                updated_data = json.load(f)

            assert "metadata" in updated_data
            assert "surrogate_disclaimer" in updated_data["metadata"]
            assert updated_data["metadata"]["surrogate_disclaimer"] == SURROGATE_DISCLAIMER

    def test_add_disclaimer_to_generalization_metrics(self):
        """Verify disclaimer is added to generalization_metrics.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            metrics_path = tmp_path / "generalization_metrics.json"

            # Create a mock metrics file without metadata
            mock_data = {
                "intra_family_mape": 4.5,
                "inter_family_mape": 12.3,
                "drop_percentage": 172.2
            }
            with open(metrics_path, 'w') as f:
                json.dump(mock_data, f)

            # Run the assertion
            run_success_criteria_assertion(
                training_logs_path=tmp_path / "nonexistent.json",
                generalization_metrics_path=metrics_path
            )

            # Verify update
            with open(metrics_path, 'r') as f:
                updated_data = json.load(f)

            assert "metadata" in updated_data
            assert "surrogate_disclaimer" in updated_data["metadata"]
            assert updated_data["metadata"]["surrogate_disclaimer"] == SURROGATE_DISCLAIMER

    def test_preserves_existing_metadata(self):
        """Verify existing metadata is preserved and disclaimer is added."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            logs_path = tmp_path / "training_logs.json"

            # Create a mock training log with existing metadata
            mock_data = {
                "epoch": 10,
                "metadata": {
                    "model_version": "v1.0",
                    "timestamp": "2026-01-01T00:00:00Z"
                }
            }
            with open(logs_path, 'w') as f:
                json.dump(mock_data, f)

            # Run the assertion
            run_success_criteria_assertion(
                training_logs_path=logs_path,
                generalization_metrics_path=tmp_path / "nonexistent.json"
            )

            # Verify update
            with open(logs_path, 'r') as f:
                updated_data = json.load(f)

            assert updated_data["metadata"]["model_version"] == "v1.0"
            assert updated_data["metadata"]["surrogate_disclaimer"] == SURROGATE_DISCLAIMER

    def test_handles_missing_files_gracefully(self):
        """Verify the function logs warnings but doesn't crash on missing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Neither file exists
            run_success_criteria_assertion(
                training_logs_path=tmp_path / "missing1.json",
                generalization_metrics_path=tmp_path / "missing2.json"
            )
            # If we got here without exception, the test passes
            assert True