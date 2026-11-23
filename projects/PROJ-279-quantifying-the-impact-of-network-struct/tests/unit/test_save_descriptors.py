import json
import csv
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Mock the env_config to avoid needing actual .env files during unit tests
@pytest.fixture
def mock_env_config():
    with patch('save_descriptors.get_processed_dir') as mock_get_dir:
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_dir.return_value = Path(tmpdir)
            yield mock_get_dir

@pytest.fixture
def sample_configs():
    """Generate sample configuration data for testing."""
    return [
        {
            "config_id": "config_001",
            "descriptors": {
                "ring_3": 10.5,
                "ring_4": 5.2,
                "q6": 0.12,
                "clustering": 0.45
            }
        },
        {
            "config_id": "config_002",
            "descriptors": {
                "ring_3": 8.1,
                "ring_4": 6.0,
                "q6": 0.15,
                "clustering": 0.50
            }
        },
        {
            "config_id": "config_003",
            "descriptors": {
                "ring_3": 12.0,
                "ring_4": 4.5,
                "q6": 0.10,
                "clustering": 0.40
            }
        }
    ]

@pytest.fixture
def aggregated_json_file(sample_configs, mock_env_config):
    """Create a temporary aggregated JSON file."""
    processed_dir = mock_env_config.return_value
    file_path = processed_dir / "aggregated_descriptors.json"
    
    data = {"configs": sample_configs}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    
    return file_path

class TestLoadProcessedConfigs:
    def test_load_success(self, aggregated_json_file, mock_env_config):
        from save_descriptors import load_processed_configs
        
        configs = load_processed_configs()
        
        assert len(configs) == 3
        assert configs[0]["config_id"] == "config_001"
        assert "descriptors" in configs[0]

    def test_load_missing_file(self, mock_env_config):
        from save_descriptors import load_processed_configs
        
        with pytest.raises(FileNotFoundError, match="Missing aggregated descriptors file"):
            load_processed_configs()

    def test_load_flat_list_format(self, sample_configs, mock_env_config):
        processed_dir = mock_env_config.return_value
        file_path = processed_dir / "aggregated_descriptors.json"
        
        # Write as flat list
        with open(file_path, 'w') as f:
            json.dump(sample_configs, f)
        
        from save_descriptors import load_processed_configs
        configs = load_processed_configs()
        
        assert len(configs) == 3

class TestSaveDescriptorsToCsv:
    def test_save_valid_data(self, sample_configs, mock_env_config):
        from save_descriptors import save_descriptors_to_csv
        
        output_path = save_descriptors_to_csv(sample_configs, "test_descriptors.csv")
        
        assert output_path.exists()
        assert output_path.name == "test_descriptors.csv"
        
        # Verify content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 3
        assert rows[0]["config_id"] == "config_001"
        assert float(rows[0]["q6"]) == pytest.approx(0.12)
        assert "ring_3" in rows[0]

    def test_save_empty_list(self, mock_env_config):
        from save_descriptors import save_descriptors_to_csv
        
        output_path = save_descriptors_to_csv([], "empty_descriptors.csv")
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
        # Should have at least the header
        assert "config_id" in content

    def test_save_handles_missing_descriptors(self, mock_env_config):
        configs = [
            {"config_id": "config_001", "descriptors": {"q6": 0.1}},
            {"config_id": "config_002"}, # Missing descriptors key
        ]
        
        from save_descriptors import save_descriptors_to_csv
        
        # Should not raise, just warn
        output_path = save_descriptors_to_csv(configs, "partial_descriptors.csv")
        assert output_path.exists()

class TestMain:
    @patch('save_descriptors.load_processed_configs')
    @patch('save_descriptors.save_descriptors_to_csv')
    def test_main_success(self, mock_save, mock_load, mock_env_config, sample_configs):
        from save_descriptors import main
        
        mock_load.return_value = sample_configs
        mock_save.return_value = Path("mock_path.csv")
        
        main()
        
        mock_load.assert_called_once()
        mock_save.assert_called_once()
        
    @patch('save_descriptors.load_processed_configs')
    def test_main_file_not_found(self, mock_load, mock_env_config):
        from save_descriptors import main
        
        mock_load.side_effect = FileNotFoundError("Test error")
        
        with pytest.raises(FileNotFoundError):
            main()