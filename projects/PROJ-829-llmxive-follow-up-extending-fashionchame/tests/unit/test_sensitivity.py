"""
Unit tests for the Sensitivity Analysis module.
"""

import pytest
import json
import csv
import tempfile
from pathlib import Path
from src.stats.sensitivity import (
    load_motion_labels,
    calculate_motion_label,
    calculate_robustness_index,
    run_sensitivity_analysis
)


class TestCalculateMotionLabel:
    def test_high_motion(self):
        assert calculate_motion_label(0.5, 0.3) == "High"

    def test_low_motion(self):
        assert calculate_motion_label(0.1, 0.3) == "Low"

    def test_boundary_condition(self):
        assert calculate_motion_label(0.3, 0.3) == "High"


class TestCalculateRobustnessIndex:
    def test_stable_labels(self):
        """Test when labels don't change between thresholds."""
        samples = [
            {'optical_flow_magnitude': 0.5},
            {'optical_flow_magnitude': 0.2},
            {'optical_flow_magnitude': 0.8}
        ]
        # Thresholds 0.3 and 0.4:
        # T=0.3: [High, Low, High]
        # T=0.4: [High, Low, High] -> All same
        thresholds = [0.3, 0.4]
        metrics = calculate_robustness_index(samples, thresholds)

        # Both should be 100% stable
        assert metrics[0.3] == 100.0
        assert metrics[0.4] == 100.0

    def test_unstable_labels(self):
        """Test when labels change between thresholds."""
        samples = [
            {'optical_flow_magnitude': 0.35} # Changes between 0.3 and 0.4
        ]
        thresholds = [0.3, 0.4]
        metrics = calculate_robustness_index(samples, thresholds)

        # T=0.3: High, T=0.4: High (0.35 >= 0.4 is False? No, 0.35 < 0.4 -> Low)
        # Wait: 0.35 >= 0.3 -> High. 0.35 >= 0.4 -> Low.
        # So at T=0.3, label is High. At T=0.4, label is Low.
        # Change detected. Stability = 0%.
        assert metrics[0.3] == 0.0
        assert metrics[0.4] == 0.0

    def test_mixed_stability(self):
        """Test with some stable and some unstable samples."""
        samples = [
            {'optical_flow_magnitude': 0.5}, # Stable (High -> High)
            {'optical_flow_magnitude': 0.2}, # Stable (Low -> Low)
            {'optical_flow_magnitude': 0.35} # Unstable (High -> Low)
        ]
        thresholds = [0.3, 0.4]
        metrics = calculate_robustness_index(samples, thresholds)

        # 2 out of 3 stable -> 66.67%
        assert abs(metrics[0.3] - 66.67) < 0.1
        assert abs(metrics[0.4] - 66.67) < 0.1


class TestRunSensitivityAnalysis:
    def test_run_creates_csv(self):
        """Test that the function creates the output CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "motion_labels.json"
            output_file = tmpdir / "sensitivity_analysis.csv"

            # Create mock input data
            samples = [
                {'optical_flow_magnitude': 0.1},
                {'optical_flow_magnitude': 0.5},
                {'optical_flow_magnitude': 0.9}
            ]
            with open(input_file, 'w') as f:
                json.dump(samples, f)

            # Run analysis
            result_path = run_sensitivity_analysis(input_file, output_file)

            assert result_path.exists()
            assert result_path == output_file

            # Verify CSV content
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) > 0
            assert 'threshold' in rows[0]
            assert 'robustness_metric' in rows[0]

    def test_empty_samples_raises_error(self):
        """Test that empty input raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "motion_labels.json"
            output_file = tmpdir / "sensitivity_analysis.csv"

            with open(input_file, 'w') as f:
                json.dump([], f)

            with pytest.raises(ValueError, match="No samples found"):
                run_sensitivity_analysis(input_file, output_file)

    def test_missing_field_raises_error(self):
        """Test that missing optical_flow_magnitude raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            input_file = tmpdir / "motion_labels.json"
            output_file = tmpdir / "sensitivity_analysis.csv"

            with open(input_file, 'w') as f:
                json.dump([{'id': 1}], f)

            with pytest.raises(ValueError, match="missing 'optical_flow_magnitude'"):
                run_sensitivity_analysis(input_file, output_file)