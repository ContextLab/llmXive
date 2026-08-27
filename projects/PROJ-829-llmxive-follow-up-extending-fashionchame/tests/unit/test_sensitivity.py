import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import csv

from src.stats.sensitivity import load_motion_labels, calculate_robustness_index, run_sensitivity_analysis

class TestSensitivityAnalysis:
    
    def test_load_motion_labels_valid_file(self):
        """Test loading motion labels from a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"frame_id": 1, "optical_flow_magnitude": 0.5, "motion_label": "High"},
                {"frame_id": 2, "optical_flow_magnitude": 0.2, "motion_label": "Low"}
            ], f)
            temp_path = Path(f.name)
        
        try:
            labels = load_motion_labels(temp_path)
            assert len(labels) == 2
            assert labels[0]["optical_flow_magnitude"] == 0.5
        finally:
            temp_path.unlink()

    def test_load_motion_labels_missing_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_motion_labels(Path("nonexistent.json"))

    def test_calculate_robustness_index_basic(self):
        """Test basic robustness index calculation."""
        motion_labels = [
            {"frame_id": 1, "optical_flow_magnitude": 0.8},
            {"frame_id": 2, "optical_flow_magnitude": 0.3},
            {"frame_id": 3, "optical_flow_magnitude": 0.9},
            {"frame_id": 4, "optical_flow_magnitude": 0.1}
        ]
        thresholds = [0.0, 0.5, 1.0]
        
        results = calculate_robustness_index(motion_labels, thresholds)
        
        # Check results structure
        assert len(results) == 2  # 3 thresholds -> 2 steps
        assert results[0][0] == 0.0
        assert results[1][0] == 0.5
        
        # Verify logic: 
        # Step 0.0 -> 0.5:
        #   0.8: High -> High (unchanged)
        #   0.3: Low -> Low (unchanged)
        #   0.9: High -> High (unchanged)
        #   0.1: Low -> Low (unchanged)
        #   Unchanged: 4/4 = 100%
        assert abs(results[0][1] - 100.0) < 0.01

    def test_calculate_robustness_index_empty_labels(self):
        """Test that ValueError is raised for empty motion labels."""
        with pytest.raises(ValueError):
            calculate_robustness_index([], [0.0, 0.5])

    def test_calculate_robustness_index_insufficient_thresholds(self):
        """Test that ValueError is raised for insufficient thresholds."""
        motion_labels = [{"frame_id": 1, "optical_flow_magnitude": 0.5}]
        with pytest.raises(ValueError):
            calculate_robustness_index(motion_labels, [0.5])

    def test_run_sensitivity_analysis_writes_csv(self):
        """Test that run_sensitivity_analysis writes the correct CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock motion labels
            motion_labels_path = Path(tmpdir) / "motion_labels.json"
            output_path = Path(tmpdir) / "sensitivity_analysis.csv"
            
            with open(motion_labels_path, 'w') as f:
                json.dump([
                    {"frame_id": 1, "optical_flow_magnitude": 0.8},
                    {"frame_id": 2, "optical_flow_magnitude": 0.3},
                    {"frame_id": 3, "optical_flow_magnitude": 0.9},
                    {"frame_id": 4, "optical_flow_magnitude": 0.1}
                ], f)
            
            run_sensitivity_analysis(
                motion_labels_path=motion_labels_path,
                output_path=output_path,
                threshold_start=0.0,
                threshold_end=0.5,
                threshold_step=0.25
            )
            
            # Verify output exists
            assert output_path.exists()
            
            # Verify CSV content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2  # 0.0 and 0.25
            assert rows[0]['threshold'] == '0.0'
            assert 'robustness_metric' in rows[0]
            assert 'robustness_metric' in rows[1]