import pytest
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

from save_descriptors import load_processed_configs, save_descriptors_to_csv, main
from config.env_config import get_processed_dir

@pytest.fixture
def mock_processed_dir(tmp_path):
    """Create a temporary directory structure and patch get_processed_dir."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    with patch('save_descriptors.get_processed_dir', return_value=data_dir):
        with patch('config.env_config.get_processed_dir', return_value=data_dir):
            yield data_dir

def test_load_processed_configs_missing_file(mock_processed_dir):
    """Test that load_processed_configs raises FileNotFoundError if input is missing."""
    with pytest.raises(FileNotFoundError):
        load_processed_configs()

def test_load_processed_configs_success(mock_processed_dir):
    """Test successful loading of aggregated descriptors."""
    input_file = mock_processed_dir / "descriptors_aggregated.json"
    test_data = [
        {"config_id": "A", "thermal_conductivity": 1.0, "ring_3": 5},
        {"config_id": "B", "thermal_conductivity": 2.0, "ring_4": 10}
    ]
    
    with open(input_file, 'w') as f:
        json.dump(test_data, f)
    
    result = load_processed_configs()
    assert result == test_data
    assert len(result) == 2

def test_save_descriptors_to_csv_empty_list(mock_processed_dir):
    """Test saving an empty list of configurations."""
    output_file = mock_processed_dir / "test_empty.csv"
    save_descriptors_to_csv([], output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        content = f.read()
    # Should be empty or just headers depending on implementation, 
    # but our implementation writes nothing if list is empty.
    # Let's verify the file exists and is empty.
    assert len(content) == 0

def test_save_descriptors_to_csv_success(mock_processed_dir):
    """Test successful saving of configurations to CSV."""
    configs = [
        {"config_id": "C1", "thermal_conductivity": 10.5, "q6": 0.4, "clustering": 0.8},
        {"config_id": "C2", "thermal_conductivity": 12.3, "q6": 0.5, "clustering": 0.7}
    ]
    output_file = mock_processed_dir / "test_success.csv"
    
    save_descriptors_to_csv(configs, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['config_id'] == 'C1'
    assert float(rows[0]['thermal_conductivity']) == 10.5
    assert float(rows[0]['q6']) == 0.4
    
    # Check headers are present
    with open(output_file, 'r') as f:
        header_line = f.readline().strip()
    headers = header_line.split(',')
    assert 'config_id' in headers
    assert 'thermal_conductivity' in headers
    assert 'q6' in headers
    assert 'clustering' in headers

def test_main_integration(mock_processed_dir, caplog):
    """Test the main function integration."""
    # Setup input
    input_file = mock_processed_dir / "descriptors_aggregated.json"
    test_data = [
        {"config_id": "M1", "thermal_conductivity": 5.0, "feature_x": 10}
    ]
    with open(input_file, 'w') as f:
        json.dump(test_data, f)
    
    # Mock compute_file_checksum to avoid actual hashing in test
    with patch('save_descriptors.compute_file_checksum', return_value="fake_checksum"):
        with patch('save_descriptors.register_artifact') as mock_reg:
            main()
    
    output_file = mock_processed_dir / "descriptors.csv"
    assert output_file.exists()
    
    # Verify register_artifact was called
    mock_reg.assert_called_once()
    args = mock_reg.call_args
    assert "descriptors.csv" in str(args)
