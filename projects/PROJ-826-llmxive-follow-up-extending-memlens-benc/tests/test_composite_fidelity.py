"""
Unit tests for T035: Composite Fidelity calculation.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Adjust import path to match project structure
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from composite_fidelity import (
    calculate_relative_improvement,
    load_json_file,
    calculate_composite_fidelity
)


class TestRelativeImprovement:
    def test_positive_improvement(self):
        # Fine 0.8, Coarse 0.5 -> (0.3)/0.5 = 0.6
        assert calculate_relative_improvement(0.5, 0.8) == pytest.approx(0.6)

    def test_negative_improvement(self):
        # Fine 0.4, Coarse 0.5 -> (-0.1)/0.5 = -0.2
        assert calculate_relative_improvement(0.5, 0.4) == pytest.approx(-0.2)

    def test_zero_improvement(self):
        assert calculate_relative_improvement(0.5, 0.5) == pytest.approx(0.0)

    def test_zero_coarse_accuracy(self):
        # Division by zero case
        assert calculate_relative_improvement(0.0, 0.5) == float('inf')
        assert calculate_relative_improvement(0.0, 0.0) == 0.0


class TestLoadJsonFile:
    def test_load_valid_file(self, tmp_path):
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}')
        result = load_json_file(test_file)
        assert result == {"key": "value"}

    def test_load_missing_file(self, tmp_path):
        missing_file = tmp_path / "missing.json"
        with pytest.raises(FileNotFoundError):
            load_json_file(missing_file)


class TestCompositeFidelityIntegration:
    @pytest.fixture
    def setup_mock_files(self, tmp_path):
        """Setup mock metrics files for testing."""
        metrics_dir = tmp_path / "data" / "processed" / "metrics"
        metrics_dir.mkdir(parents=True)
        
        # Mock detection_recall.json (VALID case: recall >= 0.6)
        detection_data = {
            "recall": 0.75,
            "summary": {"recall": 0.75}
        }
        with open(metrics_dir / "detection_recall.json", 'w') as f:
            json.dump(detection_data, f)

        # Mock final_comparison_report.json (from T026)
        report_data = {
            "coarse_accuracy": 0.50,
            "fine_accuracy": 0.70,
            "p_value": 0.01,
            "effect_size": 0.5
        }
        with open(metrics_dir / "final_comparison_report.json", 'w') as f:
            json.dump(report_data, f)

        return metrics_dir

    def test_valid_case(self, setup_mock_files, tmp_path):
        """Test case where Recall >= 0.6, pipeline should continue."""
        # Patch PROJECT_ROOT to point to tmp_path
        with patch('composite_fidelity.PROJECT_ROOT', tmp_path):
            with patch('composite_fidelity.METRICS_DIR', setup_mock_files):
                with patch('composite_fidelity.OUTPUT_FILE', setup_mock_files / "composite_fidelity.json"):
                    result = calculate_composite_fidelity()
                    
                    assert result["status"] == "VALID"
                    assert result["object_detection_recall"] == 0.75
                    assert result["relative_improvement"] == pytest.approx(0.4) # (0.7-0.5)/0.5
                    
                    # Verify file was written
                    output_path = setup_mock_files / "composite_fidelity.json"
                    assert output_path.exists()
                    
                    with open(output_path, 'r') as f:
                        saved_data = json.load(f)
                    assert saved_data["status"] == "VALID"

    def test_invalid_case(self, setup_mock_files, tmp_path):
        """Test case where Recall < 0.6, pipeline should HALT (raise error)."""
        # Modify mock to have low recall
        detection_data = {"recall": 0.40, "summary": {"recall": 0.40}}
        with open(setup_mock_files / "detection_recall.json", 'w') as f:
            json.dump(detection_data, f)

        with patch('composite_fidelity.PROJECT_ROOT', tmp_path):
            with patch('composite_fidelity.METRICS_DIR', setup_mock_files):
                with patch('composite_fidelity.OUTPUT_FILE', setup_mock_files / "composite_fidelity.json"):
                    with pytest.raises(RuntimeError, match="HALTED"):
                        calculate_composite_fidelity()

    def test_missing_accuracy_metrics(self, setup_mock_files, tmp_path):
        """Test behavior when accuracy metrics are missing."""
        # Remove the accuracy report
        (setup_mock_files / "final_comparison_report.json").unlink()
        (setup_mock_files / "accuracy_metrics.json").unlink(missing_ok=True)

        with patch('composite_fidelity.PROJECT_ROOT', tmp_path):
            with patch('composite_fidelity.METRICS_DIR', setup_mock_files):
                with patch('composite_fidelity.OUTPUT_FILE', setup_mock_files / "composite_fidelity.json"):
                    with pytest.raises(FileNotFoundError, match="Could not find accuracy metrics"):
                        calculate_composite_fidelity()
