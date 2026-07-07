"""
Tests for T025: stats_report.py
"""
import os
import csv
import tempfile
import shutil
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Mock the config module to avoid path issues in tests
import sys
from io import StringIO

# We'll test the logic by mocking the analysis functions
# and verifying the output format

@pytest.fixture
def mock_data():
    """Create a minimal valid aggregated dataset."""
    data = {
        'model_id': ['GPT2-small', 'GPT2-small', 'CodeBERT', 'CodeBERT', 'StarCoder-1B', 'StarCoder-1B'],
        'problem_id': ['prob1', 'prob2', 'prob1', 'prob2', 'prob1', 'prob2'],
        'tokens_generated': [10.0, 12.0, 8.0, 9.0, 15.0, 16.0],
        'energy_kwh': [0.001, 0.0012, 0.0008, 0.0009, 0.002, 0.0021],
        'runtime_seconds': [5.0, 6.0, 4.0, 4.5, 8.0, 8.5],
        'pass_fail_status': [1, 0, 1, 1, 0, 1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

def test_stats_report_format(temp_dir, mock_data):
    """Test that stats_report.csv is created with correct columns."""
    from code.stats_report import write_stats_report
    
    # Mock the config paths
    with patch('code.stats_report.DATA_PROCESSED_DIR', temp_dir):
        # Write mock data
        input_file = os.path.join(temp_dir, "energy_results_aggregated.csv")
        mock_data.to_csv(input_file, index=False)
        
        # Mock the analysis functions to return predictable results
        mock_anova = {"F": 12.5, "p": 0.001, "df_model": 2, "df_resid": 10}
        mock_tukey = {
            ("GPT2-small", "CodeBERT"): {"meandiff": 0.0002, "p-adj": 0.05, "confint": (0.0001, 0.0003)}
        }
        mock_regression = {"slope": 0.001, "intercept": 0.0005, "r_squared": 0.85, "p_value": 0.03}
        mock_sensitivity = {"original_p": 0.001, "perturbed_p": 0.0015, "delta_p": 0.0005, "robust": True}
        
        with patch('code.stats_report.load_data', return_value=mock_data), \
             patch('code.stats_report.run_anova', return_value=mock_anova), \
             patch('code.stats_report.run_tukey', return_value=mock_tukey), \
             patch('code.stats_report.run_regression', return_value=mock_regression), \
             patch('code.stats_report.run_sensitivity_analysis', return_value=mock_sensitivity):
            
            output_file = write_stats_report()
            
            # Verify file exists
            assert os.path.exists(output_file), f"Output file not created: {output_file}"
            
            # Verify CSV structure
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            # Check columns
            expected_columns = ["metric", "model_or_group", "value", "note"]
            assert reader.fieldnames == expected_columns, f"Columns mismatch: {reader.fieldnames}"
            
            # Check we have some rows
            assert len(rows) > 0, "Stats report is empty"
            
            # Check for key metrics
            metrics = [row['metric'] for row in rows]
            assert "ANOVA_F_value" in metrics, "Missing ANOVA F value"
            assert "ANOVA_p_value" in metrics, "Missing ANOVA p value"
            assert "Regression_slope" in metrics, "Missing regression slope"
            assert "Sensitivity_original_p" in metrics, "Missing sensitivity original p"

def test_format_statistic():
    """Test the format_statistic helper function."""
    from code.stats_report import format_statistic
    
    # Test normal float
    assert format_statistic(1.234567) == "1.234567"
    
    # Test None
    assert format_statistic(None) == ""
    
    # Test NaN
    assert format_statistic(float('nan')) == ""
    
    # Test string
    assert format_statistic("True") == "True"

def test_missing_input_file(temp_dir):
    """Test that FileNotFoundError is raised when input is missing."""
    from code.stats_report import write_stats_report
    
    with patch('code.stats_report.DATA_PROCESSED_DIR', temp_dir):
        with pytest.raises(FileNotFoundError):
            write_stats_report()