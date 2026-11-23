"""
Tests for Power Limitation Check (Task T028)
"""
import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path

# Import functions to test
from check_power_limitation import (
    load_data,
    get_predictor_count,
    check_power_limitation,
    write_warning_message
)

class TestPowerLimitation:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_data_existing_file(self):
        """Test loading an existing CSV file."""
        csv_path = os.path.join(self.temp_dir, "test_networks.csv")
        df_test = pd.DataFrame({
            'id': [1, 2, 3],
            'class': ['random', 'scale_free', 'small_world'],
            'N': [100, 100, 100]
        })
        df_test.to_csv(csv_path, index=False)
        
        loaded_df = load_data(csv_path)
        
        assert loaded_df is not None
        assert len(loaded_df) == 3
        assert 'class' in loaded_df.columns

    def test_load_data_missing_file(self):
        """Test loading a non-existent file."""
        loaded_df = load_data("non_existent_file.csv")
        assert loaded_df is None

    def test_check_power_limitation_pass(self):
        """Test check passing with sufficient data."""
        df = pd.DataFrame({
            'id': list(range(50)),
            'class': (['random'] * 10 + 
                     ['scale_free'] * 10 + 
                     ['small_world'] * 10 + 
                     ['lattice'] * 10 + 
                     ['star'] * 10)
        })
        
        result = check_power_limitation(df, min_samples=50, min_per_class=10)
        
        assert result['passed'] is True
        assert result['total'] == 50
        assert result['reason'] == "Power requirement satisfied"

    def test_check_power_limitation_fail_total(self):
        """Test check failing due to insufficient total samples."""
        df = pd.DataFrame({
            'id': list(range(40)),
            'class': (['random'] * 8 + 
                     ['scale_free'] * 8 + 
                     ['small_world'] * 8 + 
                     ['lattice'] * 8 + 
                     ['star'] * 8)
        })
        
        result = check_power_limitation(df, min_samples=50, min_per_class=10)
        
        assert result['passed'] is False
        assert "Total samples" in result['reason']
        assert "40" in result['reason']

    def test_check_power_limitation_fail_class(self):
        """Test check failing due to insufficient samples in one class."""
        df = pd.DataFrame({
            'id': list(range(50)),
            'class': (['random'] * 10 + 
                     ['scale_free'] * 10 + 
                     ['small_world'] * 10 + 
                     ['lattice'] * 10 + 
                     ['star'] * 10)
        })
        # Modify one row to create an imbalance
        df.loc[49, 'class'] = 'random' # Now star has 9, random has 11
        
        result = check_power_limitation(df, min_samples=50, min_per_class=10)
        
        assert result['passed'] is False
        assert "star" in result['reason']

    def test_write_warning_message(self):
        """Test writing the warning file."""
        output_path = os.path.join(self.temp_dir, "power_warning.txt")
        result = {
            'passed': False,
            'total': 40,
            'per_class': {'random': 8, 'scale_free': 8, 'small_world': 8, 'lattice': 8, 'star': 8},
            'reason': "Total samples (40) < required (50)"
        }
        
        write_warning_message(output_path, result)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "POWER LIMITATION WARNING" in content
        assert "Status: FAILED" in content
        assert "Total Samples: 40" in content
        assert "ACTION REQUIRED" in content

    def test_check_power_limitation_missing_column(self):
        """Test check failing when 'class' column is missing."""
        df = pd.DataFrame({
            'id': list(range(50)),
            'N': [100] * 50
        })
        
        result = check_power_limitation(df, min_samples=50, min_per_class=10)
        
        assert result['passed'] is False
        assert "class" in result['reason'].lower()