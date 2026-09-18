import os
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Import the functions to test
from model_report import calculate_empirical_p_value, compute_null_distribution_stats, generate_model_report, load_existing_results

class TestEmpiricalPValue:
    def test_p_value_calculation_basic(self):
        """Test basic p-value calculation with known values."""
        observed_mae = 0.5
        null_maes = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1])
        
        # Count <= 0.5: 0.1, 0.2, 0.3, 0.4 -> 4 items
        # p = (4 + 1) / (10 + 1) = 5/11
        expected_p = 5 / 11
        
        p_value = calculate_empirical_p_value(observed_mae, null_maes)
        assert abs(p_value - expected_p) < 1e-6

    def test_p_value_all_lower(self):
        """Test when all null values are lower than observed."""
        observed_mae = 10.0
        null_maes = np.array([1.0, 2.0, 3.0])
        
        # Count <= 10: 3 items
        # p = (3 + 1) / (3 + 1) = 1.0
        p_value = calculate_empirical_p_value(observed_mae, null_maes)
        assert p_value == 1.0

    def test_p_value_all_higher(self):
        """Test when all null values are higher than observed."""
        observed_mae = 0.0
        null_maes = np.array([1.0, 2.0, 3.0])
        
        # Count <= 0: 0 items
        # p = (0 + 1) / (3 + 1) = 0.25
        p_value = calculate_empirical_p_value(observed_mae, null_maes)
        assert abs(p_value - 0.25) < 1e-6

    def test_p_value_empty_null(self):
        """Test that empty null distribution raises error."""
        observed_mae = 0.5
        null_maes = np.array([])
        
        with pytest.raises(ValueError):
            calculate_empirical_p_value(observed_mae, null_maes)

class TestNullDistributionStats:
    def test_stats_calculation(self):
        """Test calculation of null distribution statistics."""
        null_maes = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        stats = compute_null_distribution_stats(null_maes)
        
        assert stats["mean_mae"] == 3.0
        assert stats["std_mae"] == pytest.approx(np.std(null_maes))
        assert stats["min_mae"] == 1.0
        assert stats["max_mae"] == 5.0
        assert stats["count"] == 5

class TestModelReportGeneration:
    def test_report_generation(self):
        """Test generation of model report JSON."""
        observed_stats = {"mae": 0.5, "r2": 0.3}
        null_stats = {"mean_mae": 0.6, "std_mae": 0.1}
        p_value = 0.03
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            output_path = f.name
        
        try:
            report = generate_model_report(observed_stats, null_stats, p_value, output_path)
            
            # Verify file exists and content matches
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            
            assert saved_report["empirical_p_value"] == p_value
            assert saved_report["observed_stats"]["mae"] == 0.5
            assert saved_report["interpretation"] == "Significant"
        finally:
            os.unlink(output_path)

class TestLoadExistingResults:
    def test_load_valid_file(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"observed_stats": {"mae": 0.5}}, f)
            temp_path = f.name
        
        try:
            data = load_existing_results(temp_path)
            assert data["observed_stats"]["mae"] == 0.5
        finally:
            os.unlink(temp_path)

    def test_load_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_existing_results("nonexistent_file.json")