import pytest
import os
import json
import yaml
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from interpret import load_threshold_justification

class TestLoadThresholdJustification:
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Create a temporary config.yaml for testing."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "thresholds": {
                "r2": {
                    "citation": "Test Citation 2024",
                    "value": 0.70,
                    "sweep_range": [0.70, 0.75, 0.80]
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        return config_file

    def test_load_justification_success(self, temp_config_dir):
        """Test that justification is loaded correctly."""
        result = load_threshold_justification(str(temp_config_dir))
        assert result == "Test Citation 2024"

    def test_load_justification_missing_file(self):
        """Test that FileNotFoundError is raised if config is missing."""
        with pytest.raises(FileNotFoundError):
            load_threshold_justification("non_existent_config.yaml")

    def test_load_justification_missing_key(self, tmp_path):
        """Test that KeyError is raised if 'thresholds.r2.citation' is missing."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "thresholds": {
                "r2": {
                    "value": 0.70
                    # Missing citation
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(KeyError):
            load_threshold_justification(str(config_file))

    def test_load_justification_empty_citation(self, tmp_path):
        """Test that ValueError is raised if citation is empty."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "thresholds": {
                "r2": {
                    "citation": ""
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        with pytest.raises(ValueError):
            load_threshold_justification(str(config_file))
