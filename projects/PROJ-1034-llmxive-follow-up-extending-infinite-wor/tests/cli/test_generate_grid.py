"""
Unit tests for the parameter grid generator (T023a).
"""
import pytest
import os
import csv
import tempfile
import sys
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from cli.generate_grid import generate_combinations, write_grid_csv, PARAM_RANGES

class TestGenerateGrid:
    def test_generate_combinations_count(self):
        """Verify the total number of generated combinations matches expectation."""
        configs = list(generate_combinations())
        
        # Expected count = len(locality) * len(memory) * len(non_linearity)
        expected = (
            len(PARAM_RANGES['locality']) * 
            len(PARAM_RANGES['memory']) * 
            len(PARAM_RANGES['non_linearity'])
        )
        
        assert len(configs) == expected
        assert expected > 0  # Ensure we aren't testing an empty grid

    def test_generate_combinations_structure(self):
        """Verify each generated config has the correct keys and types."""
        configs = list(generate_combinations())
        
        required_keys = {'locality', 'memory', 'non_linearity'}
        
        for config in configs:
            assert set(config.keys()) == required_keys
            assert isinstance(config['locality'], int)
            assert isinstance(config['memory'], int)
            assert isinstance(config['non_linearity'], float)
            
            # Verify values are within expected ranges
            assert config['locality'] in PARAM_RANGES['locality']
            assert config['memory'] in PARAM_RANGES['memory']
            assert config['non_linearity'] in PARAM_RANGES['non_linearity']

    def test_write_grid_csv(self):
        """Verify the CSV writing functionality."""
        configs = list(generate_combinations())
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
        
        try:
            write_grid_csv(configs, tmp_path)
            
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == len(configs)
            
            # Check header
            assert set(rows[0].keys()) == {'locality', 'memory', 'non_linearity'}
            
            # Check first row data integrity
            first_config = configs[0]
            first_row = rows[0]
            assert int(first_row['locality']) == first_config['locality']
            assert int(first_row['memory']) == first_config['memory']
            assert float(first_row['non_linearity']) == first_config['non_linearity']
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_write_grid_csv_empty(self):
        """Verify that writing an empty list raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            tmp_path = tmp.name
        
        try:
            with pytest.raises(ValueError):
                write_grid_csv([], tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_output_directory_creation(self):
        """Verify that the script creates the output directory if it doesn't exist."""
        configs = list(generate_combinations())
        
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, 'subdir', 'nested', 'grid.csv')
            
            write_grid_csv(configs, nested_path)
            
            assert os.path.exists(nested_path)