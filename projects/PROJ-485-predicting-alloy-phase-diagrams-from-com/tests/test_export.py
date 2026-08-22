import os
import sys
import csv
import tempfile
import shutil
import pytest

# Add code/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features.export_descriptors import load_processed_data, write_csv_output, REQUIRED_COLUMNS
from utils.error_codes import ErrorCode

class TestExportDescriptors:
    """Tests for T018: Write processed data to data/processed/descriptors.csv with schema compliance"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_schema_compliance(self, temp_dir):
        """Verify that the output CSV contains all required columns"""
        # Create a mock input file
        input_path = os.path.join(temp_dir, 'input.csv')
        output_path = os.path.join(temp_dir, 'output.csv')
        
        mock_data = [
            {
                'system_id': 'Cu-Zn',
                'composition': '50-50',
                'temperature': 1000.0,
                'phase': 'alpha',
                'mean_atomic_radius': 1.28,
                'electronegativity_variance': 0.05,
                'valence_electron_count': 1.5,
                'hume_rothery_concentration': 0.45
            }
        ]
        
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerows(mock_data)
        
        # Load and write
        data = load_processed_data(input_path)
        write_csv_output(data, output_path)
        
        # Verify output
        assert os.path.exists(output_path)
        
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == REQUIRED_COLUMNS
            
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['system_id'] == 'Cu-Zn'
            assert float(rows[0]['temperature']) == 1000.0

    def test_missing_input_file_raises_error(self, temp_dir):
        """Verify that missing input file raises FileNotFoundError"""
        input_path = os.path.join(temp_dir, 'nonexistent.csv')
        
        with pytest.raises(FileNotFoundError):
            load_processed_data(input_path)

    def test_invalid_schema_raises_error(self, temp_dir):
        """Verify that invalid schema raises ValueError"""
        input_path = os.path.join(temp_dir, 'bad_schema.csv')
        
        # Write CSV with missing column
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['system_id', 'composition'])
            writer.writeheader()
            writer.writerow({'system_id': 'Cu-Zn', 'composition': '50-50'})
        
        with pytest.raises(ValueError):
            load_processed_data(input_path)

    def test_numeric_conversion(self, temp_dir):
        """Verify that string numbers are converted to floats"""
        input_path = os.path.join(temp_dir, 'input.csv')
        output_path = os.path.join(temp_dir, 'output.csv')
        
        # Write with string numbers
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            writer.writerow({
                'system_id': 'Al-Cu',
                'composition': '70-30',
                'temperature': '900',  # String
                'phase': 'theta',
                'mean_atomic_radius': '1.43',
                'electronegativity_variance': '0.1',
                'valence_electron_count': '3.0',
                'hume_rothery_concentration': '0.5'
            })
        
        data = load_processed_data(input_path)
        
        # Check conversion
        assert isinstance(data[0]['temperature'], float)
        assert data[0]['temperature'] == 900.0
        assert isinstance(data[0]['mean_atomic_radius'], float)
        
        write_csv_output(data, output_path)
        
        # Verify written values
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert float(row['temperature']) == 900.0

    def test_empty_data_handling(self, temp_dir):
        """Verify handling of empty dataset"""
        input_path = os.path.join(temp_dir, 'input.csv')
        output_path = os.path.join(temp_dir, 'output.csv')
        
        # Write header only
        with open(input_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        
        data = load_processed_data(input_path)
        assert len(data) == 0
        
        # Should still create file with headers
        write_csv_output(data, output_path)
        assert os.path.exists(output_path)
        
        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            assert list(reader.fieldnames) == REQUIRED_COLUMNS
            rows = list(reader)
            assert len(rows) == 0
