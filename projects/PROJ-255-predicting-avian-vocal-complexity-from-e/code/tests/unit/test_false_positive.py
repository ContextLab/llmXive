import os
import sys
import tempfile
import csv
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.false_positive import (
    load_sensitivity_threshold_data,
    estimate_false_positive_rate_variation,
    save_false_positive_analysis
)
from src.utils.config import get_processed_data_dir

class TestFalsePositiveAnalysis:
    
    def test_load_sensitivity_threshold_data(self, tmp_path):
        """Test loading of sensitivity summary data."""
        # Create a mock sensitivity_summary.csv
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        input_file = processed_dir / "sensitivity_summary.csv"
        
        data = [
            {"threshold": "5", "sample_size": "100", "correlation_r": "0.5", "variation_percent": "2.0"},
            {"threshold": "10", "sample_size": "95", "correlation_r": "0.48", "variation_percent": "1.5"},
            {"threshold": "15", "sample_size": "90", "correlation_r": "0.45", "variation_percent": "3.0"}
        ]
        
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["threshold", "sample_size", "correlation_r", "variation_percent"])
            writer.writeheader()
            writer.writerows(data)
        
        # Patch get_processed_data_dir to return our temp dir
        with patch('src.analysis.false_positive.get_processed_data_dir', return_value=processed_dir):
            loaded_data = load_sensitivity_threshold_data()
            
        assert len(loaded_data) == 3
        assert loaded_data[0]['threshold'] == 5
        assert loaded_data[0]['sample_size'] == 100
        assert loaded_data[0]['correlation_r'] == 0.5
        assert loaded_data[1]['threshold'] == 10
        
    def test_estimate_false_positive_rate_variation(self):
        """Test the core logic of FPR variation estimation."""
        # Mock data
        data = [
            {"threshold": 5, "sample_size": 100, "correlation_r": 0.5, "variation_percent": 2.0},
            {"threshold": 10, "sample_size": 95, "correlation_r": 0.48, "variation_percent": 1.5},
            {"threshold": 15, "sample_size": 90, "correlation_r": 0.45, "variation_percent": 3.0}
        ]
        
        results = estimate_false_positive_rate_variation(data, baseline_threshold=10)
        
        assert results['baseline_threshold'] == 10
        assert results['baseline_correlation_r'] == 0.48
        assert len(results['analysis_results']) == 3
        
        # Check results for threshold 10 (baseline)
        baseline_result = next(r for r in results['analysis_results'] if r['threshold'] == 10)
        assert baseline_result['deviation_from_baseline_percent'] == 0.0
        assert baseline_result['estimated_fpr_variation_percent'] == 0.0
        
        # Check stability summary
        assert 'max_deviation_percent' in results['stability_summary']
        assert 'is_stable' in results['stability_summary']
        
    def test_estimate_fpr_with_zero_baseline(self):
        """Test behavior when baseline correlation is 0."""
        data = [
            {"threshold": 10, "sample_size": 95, "correlation_r": 0.0, "variation_percent": 0.0},
            {"threshold": 15, "sample_size": 90, "correlation_r": 0.1, "variation_percent": 1.0}
        ]
        
        results = estimate_false_positive_rate_variation(data, baseline_threshold=10)
        
        assert results['baseline_correlation_r'] == 0.0
        # When baseline is 0, deviation should be absolute difference
        # |0.1 - 0.0| = 0.1 -> 0.1 * 100 = 10.0 (if we treat as percent) or just 0.1
        # In our code: if use_absolute, deviation = abs(0.1 - 0.0) = 0.1
        # Then estimated_fpr_variation = 0.1
        # Wait, the code does: deviation = abs(current - base)
        # Then estimated_fpr_variation = deviation
        # So deviation is 0.1.
        
        threshold_15_result = next(r for r in results['analysis_results'] if r['threshold'] == 15)
        assert threshold_15_result['deviation_from_baseline_percent'] == 0.1
        
    def test_save_false_positive_analysis(self, tmp_path):
        """Test saving results to JSON."""
        results = {
            "baseline_threshold": 10,
            "baseline_correlation_r": 0.48,
            "analysis_results": [
                {"threshold": 10, "sample_size": 95, "correlation_r": 0.48, "deviation_from_baseline_percent": 0.0, "estimated_fpr_variation_percent": 0.0}
            ],
            "stability_summary": {"max_deviation_percent": 0.0, "mean_deviation_percent": 0.0, "is_stable": True, "stability_threshold_percent": 10.0}
        }
        
        output_file = tmp_path / "test_output.json"
        
        returned_path = save_false_positive_analysis(results, output_path=output_file)
        
        assert returned_path == output_file
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results
        
    def test_file_not_found(self, tmp_path):
        """Test error handling when input file is missing."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        # Don't create the file
        with patch('src.analysis.false_positive.get_processed_data_dir', return_value=processed_dir):
            with pytest.raises(FileNotFoundError):
                load_sensitivity_threshold_data()