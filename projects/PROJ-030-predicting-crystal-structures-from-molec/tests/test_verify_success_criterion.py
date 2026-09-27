"""
Tests for the success criterion verification module (T017c).
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from modeling.verify_success_criterion import verify_success_criterion, calculate_lift

class TestVerifySuccessCriterion:
    """Test cases for verify_success_criterion function."""

    def test_calculate_lift(self):
        """Test the lift calculation helper."""
        assert calculate_lift(0.8, 0.6) == 0.2
        assert calculate_lift(0.5, 0.5) == 0.0
        assert calculate_lift(0.4, 0.6) == -0.2

    def test_verification_passed(self, tmp_path):
        """Test that verification passes when model accuracy is sufficiently higher."""
        # Create temporary input files
        model_metrics = {
            "Accuracy": 0.75,
            "F1_Macro": 0.70
        }
        baseline_metrics = {
            "Accuracy": 0.60,
            "Method": "Majority Class"
        }

        model_path = tmp_path / "model_metrics.json"
        baseline_path = tmp_path / "baseline_metrics.json"
        output_path = tmp_path / "result.json"

        with open(model_path, 'w') as f:
            json.dump(model_metrics, f)
        
        with open(baseline_path, 'w') as f:
            json.dump(baseline_metrics, f)

        # Run verification with a threshold of 0.10 (0.60 + 0.10 = 0.70 < 0.75)
        result = verify_success_criterion(
            model_path,
            baseline_path,
            output_path,
            deferred_threshold=0.10
        )

        assert result["passed"] is True
        assert result["lift"] == 0.15
        assert result["required_threshold"] == 0.70

        # Verify file was written
        assert output_path.exists()
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
        assert saved_result["passed"] is True

    def test_verification_failed(self, tmp_path):
        """Test that verification fails when model accuracy is not sufficiently higher."""
        model_metrics = {
            "Accuracy": 0.62,
            "F1_Macro": 0.55
        }
        baseline_metrics = {
            "Accuracy": 0.60,
            "Method": "Majority Class"
        }

        model_path = tmp_path / "model_metrics.json"
        baseline_path = tmp_path / "baseline_metrics.json"
        output_path = tmp_path / "result.json"

        with open(model_path, 'w') as f:
            json.dump(model_metrics, f)
        
        with open(baseline_path, 'w') as f:
            json.dump(baseline_metrics, f)

        # Run verification with a threshold of 0.10 (0.60 + 0.10 = 0.70 > 0.62)
        result = verify_success_criterion(
            model_path,
            baseline_path,
            output_path,
            deferred_threshold=0.10
        )

        assert result["passed"] is False
        assert result["lift"] == 0.02
        assert result["required_threshold"] == 0.70

    def test_missing_file_raises(self, tmp_path):
        """Test that missing input files raise FileNotFoundError."""
        model_path = tmp_path / "nonexistent.json"
        baseline_path = tmp_path / "baseline.json"
        output_path = tmp_path / "result.json"

        # Create baseline but not model
        with open(baseline_path, 'w') as f:
            json.dump({"Accuracy": 0.6}, f)

        with pytest.raises(FileNotFoundError):
            verify_success_criterion(model_path, baseline_path, output_path)

    def test_missing_accuracy_raises(self, tmp_path):
        """Test that missing Accuracy key raises ValueError."""
        model_metrics = {"F1": 0.7} # No accuracy
        baseline_metrics = {"Accuracy": 0.6}

        model_path = tmp_path / "model.json"
        baseline_path = tmp_path / "baseline.json"
        output_path = tmp_path / "result.json"

        with open(model_path, 'w') as f:
            json.dump(model_metrics, f)
        
        with open(baseline_path, 'w') as f:
            json.dump(baseline_metrics, f)

        with pytest.raises(ValueError):
            verify_success_criterion(model_path, baseline_path, output_path)
