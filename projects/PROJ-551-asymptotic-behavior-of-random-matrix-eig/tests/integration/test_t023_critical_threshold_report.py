"""
Integration test for T023: Critical Threshold Report Generation.

This test verifies that:
1. The critical_threshold_report.py script runs successfully
2. It produces the expected output file
3. The output file contains the correct schema
4. The values are extracted correctly from the input
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.critical_threshold_report import (
    load_threshold_identification_results,
    generate_report_content,
    write_report
)

class TestT023CriticalThresholdReport:
    """Tests for T023 critical threshold report generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_input_data(self):
        """Create mock threshold identification data."""
        return {
            "theta_c": 2.05,
            "confidence_interval": {
                "lower": 1.98,
                "upper": 2.12
            },
            "model_params": {
                "intercept": -10.5,
                "slope": 5.2,
                "n_iterations": 156
            },
            "fit_quality": {
                "log_likelihood": -45.2,
                "residual_sum_squares": 0.0012,
                "r_squared": 0.987
            }
        }

    def test_load_threshold_identification_results(self, temp_dir, mock_input_data):
        """Test loading threshold identification results."""
        input_path = temp_dir / 'threshold_identification.json'
        
        with open(input_path, 'w') as f:
            json.dump(mock_input_data, f)
        
        loaded = load_threshold_identification_results(input_path)
        
        assert loaded['theta_c'] == mock_input_data['theta_c']
        assert loaded['confidence_interval'] == mock_input_data['confidence_interval']
        assert loaded['model_params'] == mock_input_data['model_params']

    def test_load_threshold_identification_missing_file(self, temp_dir):
        """Test that missing file raises FileNotFoundError."""
        input_path = temp_dir / 'nonexistent.json'
        
        with pytest.raises(FileNotFoundError):
            load_threshold_identification_results(input_path)

    def test_load_threshold_identification_missing_theta_c(self, temp_dir):
        """Test that missing theta_c raises ValueError."""
        input_path = temp_dir / 'bad_data.json'
        bad_data = {"confidence_interval": {"lower": 1.0, "upper": 2.0}}
        
        with open(input_path, 'w') as f:
            json.dump(bad_data, f)
        
        with pytest.raises(ValueError):
            load_threshold_identification_results(input_path)

    def test_generate_report_content(self, mock_input_data):
        """Test report content generation."""
        timestamp = datetime.now(timezone.utc)
        
        report = generate_report_content(
            theta_c=mock_input_data['theta_c'],
            confidence_interval=mock_input_data['confidence_interval'],
            model_params=mock_input_data['model_params'],
            fit_quality=mock_input_data['fit_quality'],
            timestamp=timestamp
        )
        
        assert report['report_type'] == 'critical_threshold_analysis'
        assert report['spec_objective'] == 4
        assert report['task_id'] == 'T023'
        assert 'generated_at' in report
        assert report['results']['theta_c'] == mock_input_data['theta_c']
        assert report['results']['confidence_interval'] == mock_input_data['confidence_interval']
        assert 'interpretation' in report['results']
        assert report['metadata']['model_parameters'] == mock_input_data['model_params']

    def test_write_report(self, temp_dir, mock_input_data):
        """Test writing report to file."""
        timestamp = datetime.now(timezone.utc)
        report = generate_report_content(
            theta_c=mock_input_data['theta_c'],
            confidence_interval=mock_input_data['confidence_interval'],
            model_params=mock_input_data['model_params'],
            fit_quality=mock_input_data['fit_quality'],
            timestamp=timestamp
        )
        
        output_path = temp_dir / 'critical_threshold_report.json'
        write_report(report, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report['results']['theta_c'] == mock_input_data['theta_c']
        assert loaded_report['results']['confidence_interval'] == mock_input_data['confidence_interval']

    def test_full_pipeline_simulation(self, temp_dir, mock_input_data):
        """Simulate the full T021c -> T023 pipeline."""
        # Step 1: Create input file (simulating T021c output)
        input_path = temp_dir / 'threshold_identification.json'
        with open(input_path, 'w') as f:
            json.dump(mock_input_data, f)
        
        # Step 2: Load and process (simulating T023)
        loaded_data = load_threshold_identification_results(input_path)
        timestamp = datetime.now(timezone.utc)
        report = generate_report_content(
            theta_c=loaded_data['theta_c'],
            confidence_interval=loaded_data['confidence_interval'],
            model_params=loaded_data.get('model_params', {}),
            fit_quality=loaded_data.get('fit_quality', {}),
            timestamp=timestamp
        )
        
        # Step 3: Write output
        output_path = temp_dir / 'critical_threshold_report.json'
        write_report(report, output_path)
        
        # Step 4: Verify output
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            final_report = json.load(f)
        
        # Verify schema
        assert 'report_type' in final_report
        assert 'results' in final_report
        assert 'theta_c' in final_report['results']
        assert 'confidence_interval' in final_report['results']
        assert 'interpretation' in final_report['results']
        assert 'metadata' in final_report
        
        # Verify values
        assert final_report['results']['theta_c'] == mock_input_data['theta_c']
        assert final_report['results']['confidence_interval'] == mock_input_data['confidence_interval']