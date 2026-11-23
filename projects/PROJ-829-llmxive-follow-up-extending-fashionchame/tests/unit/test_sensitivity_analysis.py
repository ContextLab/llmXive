"""
Unit tests for the sensitivity analysis module.

Tests for T035: Implement Sensitivity Analysis (Robustness Index)
"""
import pytest
import json
import tempfile
from pathlib import Path
from src.stats.sensitivity import (
    load_motion_labels,
    calculate_robustness_index,
    run_sensitivity_analysis
)

class TestLoadMotionLabels:
    """Tests for load_motion_labels function."""
    
    def test_load_valid_labels(self, tmp_path):
        """Test loading valid motion labels."""
        # Create test data
        test_data = [
            {'frame_id': 1, 'optical_flow_magnitude': 50.0, 'motion_label': 'High'},
            {'frame_id': 2, 'optical_flow_magnitude': 10.0, 'motion_label': 'Low'},
            {'frame_id': 3, 'optical_flow_magnitude': 75.0, 'motion_label': 'High'}
        ]
        
        # Write to temporary file
        test_file = tmp_path / 'motion_labels.json'
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load and verify
        loaded = load_motion_labels(str(test_file))
        assert len(loaded) == 3
        assert loaded[0]['frame_id'] == 1
        assert loaded[1]['optical_flow_magnitude'] == 10.0
    
    def test_load_empty_file(self, tmp_path):
        """Test loading an empty motion labels file."""
        test_file = tmp_path / 'motion_labels.json'
        with open(test_file, 'w') as f:
            json.dump([], f)
        
        loaded = load_motion_labels(str(test_file))
        assert len(loaded) == 0
    
    def test_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_motion_labels(str(tmp_path / 'nonexistent.json'))

class TestCalculateRobustnessIndex:
    """Tests for calculate_robustness_index function."""
    
    def test_all_labels_unchanged(self):
        """Test when all labels remain unchanged between thresholds."""
        labels = [
            {'optical_flow_magnitude': 50.0},
            {'optical_flow_magnitude': 60.0},
            {'optical_flow_magnitude': 70.0}
        ]
        
        # All magnitudes are >= 50 and >= 40, so all should be 'High' -> 'High'
        robustness = calculate_robustness_index(labels, 50.0, 40.0)
        assert robustness == 100.0
    
    def test_all_labels_changed(self):
        """Test when all labels change between thresholds."""
        labels = [
            {'optical_flow_magnitude': 45.0},  # High at 40, Low at 50
            {'optical_flow_magnitude': 55.0},  # High at 50, Low at 60? No, still High at 60
            {'optical_flow_magnitude': 35.0}   # Low at 40, Low at 30
        ]
        
        # Let's create a clearer case
        labels = [
            {'optical_flow_magnitude': 45.0},  # Low at 50, High at 40 -> CHANGED
        ]
        
        robustness = calculate_robustness_index(labels, 50.0, 40.0)
        assert robustness == 0.0
    
    def test_mixed_labels(self):
        """Test with a mix of changed and unchanged labels."""
        labels = [
            {'optical_flow_magnitude': 30.0},  # Low at 40, Low at 50 -> Unchanged
            {'optical_flow_magnitude': 45.0},  # High at 40, Low at 50 -> Changed
            {'optical_flow_magnitude': 60.0}   # High at 40, High at 50 -> Unchanged
        ]
        
        robustness = calculate_robustness_index(labels, 50.0, 40.0)
        # 2 unchanged out of 3 = 66.67%
        assert abs(robustness - 66.67) < 0.01
    
    def test_empty_labels(self):
        """Test with empty labels list."""
        robustness = calculate_robustness_index([], 50.0, 40.0)
        assert robustness == 0.0
    
    def test_missing_magnitude(self):
        """Test with samples missing optical_flow_magnitude."""
        labels = [
            {'frame_id': 1},  # No magnitude
            {'optical_flow_magnitude': 50.0}
        ]
        
        # Missing magnitude defaults to 0.0 -> Low at both thresholds
        robustness = calculate_robustness_index(labels, 50.0, 40.0)
        assert robustness == 100.0  # Both are Low -> Unchanged

class TestRunSensitivityAnalysis:
    """Tests for run_sensitivity_analysis function."""
    
    def test_full_analysis(self, tmp_path):
        """Test running a complete sensitivity analysis."""
        # Create test motion labels
        test_labels = [
            {'frame_id': i, 'optical_flow_magnitude': float(i * 10)}
            for i in range(1, 11)  # Magnitudes: 10, 20, ..., 100
        ]
        
        input_file = tmp_path / 'motion_labels.json'
        with open(input_file, 'w') as f:
            json.dump(test_labels, f)
        
        output_file = tmp_path / 'sensitivity_analysis.csv'
        
        # Run analysis
        summary = run_sensitivity_analysis(str(input_file), str(output_file))
        
        # Verify output file exists
        assert output_file.exists()
        
        # Verify summary
        assert summary['total_samples'] == 10
        assert summary['num_steps'] > 0
        assert 'min_robustness' in summary
        assert 'max_robustness' in summary
        
        # Verify CSV content
        with open(output_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 1  # Header + data rows
            assert 'threshold' in lines[0]
            assert 'robustness_metric' in lines[0]
    
    def test_empty_labels_error(self, tmp_path):
        """Test that ValueError is raised for empty labels."""
        input_file = tmp_path / 'motion_labels.json'
        with open(input_file, 'w') as f:
            json.dump([], f)
        
        output_file = tmp_path / 'sensitivity_analysis.csv'
        
        with pytest.raises(ValueError, match="No motion labels found"):
            run_sensitivity_analysis(str(input_file), str(output_file))
    
    def test_output_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        test_labels = [{'optical_flow_magnitude': 50.0}]
        
        input_file = tmp_path / 'motion_labels.json'
        with open(input_file, 'w') as f:
            json.dump(test_labels, f)
        
        output_file = tmp_path / 'subdir' / 'deep' / 'sensitivity_analysis.csv'
        
        summary = run_sensitivity_analysis(str(input_file), str(output_file))
        assert output_file.exists()
        assert summary['total_samples'] == 1