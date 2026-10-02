"""
Unit tests for the configuration loader.

Tests verify that config_loader correctly loads and validates
seeds.yaml and paths.yaml configurations.
"""

import pytest
import yaml
import os
import tempfile
from pathlib import Path

from utils.config_loader import (
    load_yaml_config,
    validate_seeds_config,
    validate_paths_config,
    verify_all_keys_exist,
    DataInsufficientError,
    CorrosionPipelineError
)


class TestLoadYamlConfig:
    """Tests for load_yaml_config function."""
    
    def test_load_valid_yaml(self, tmp_path):
        """Test loading a valid YAML file."""
        config_file = tmp_path / "test.yaml"
        config_data = {"key": "value", "number": 42}
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        result = load_yaml_config(str(config_file))
        
        assert result == config_data
        
    def test_load_empty_file_raises(self, tmp_path):
        """Test that an empty YAML file raises an error."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        
        with pytest.raises(CorrosionPipelineError):
            load_yaml_config(str(config_file))
            
    def test_load_nonexistent_file_raises(self):
        """Test that a nonexistent file raises an error."""
        with pytest.raises(CorrosionPipelineError):
            load_yaml_config("nonexistent_file.yaml")
            
    def test_load_invalid_yaml_raises(self, tmp_path):
        """Test that invalid YAML raises an error."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(CorrosionPipelineError):
            load_yaml_config(str(config_file))


class TestValidateSeedsConfig:
    """Tests for validate_seeds_config function."""
    
    def test_valid_seeds_config(self):
        """Test validation of a valid seeds configuration."""
        config = {
            "seeds": {
                "global_seed": 42,
                "model_training_seed": 123
            }
        }
        
        # Should not raise
        validate_seeds_config(config)
        
    def test_missing_seeds_key(self):
        """Test that missing 'seeds' key raises error."""
        config = {}
        
        with pytest.raises(DataInsufficientError):
            validate_seeds_config(config)
            
    def test_seeds_not_dict(self):
        """Test that non-dict seeds raises error."""
        config = {"seeds": "not_a_dict"}
        
        with pytest.raises(DataInsufficientError):
            validate_seeds_config(config)
            
    def test_empty_seeds(self):
        """Test that empty seeds dict raises error."""
        config = {"seeds": {}}
        
        with pytest.raises(DataInsufficientError):
            validate_seeds_config(config)
            
    def test_missing_global_seed(self):
        """Test that missing global_seed raises error."""
        config = {"seeds": {"model_training_seed": 42}}
        
        with pytest.raises(DataInsufficientError):
            validate_seeds_config(config)
            
    def test_none_seed_value(self):
        """Test that None seed value raises error."""
        config = {"seeds": {"global_seed": None}}
        
        with pytest.raises(DataInsufficientError):
            validate_seeds_config(config)
            
    def test_non_integer_seed_value(self):
        """Test that non-integer seed value raises error."""
        config = {"seeds": {"global_seed": "forty-two"}}
        
        with pytest.raises(DataInsufficientError):
            validate_seeds_config(config)


class TestValidatePathsConfig:
    """Tests for validate_paths_config function."""
    
    def test_valid_paths_config(self):
        """Test validation of a valid paths configuration."""
        config = {
            "paths": {
                "root": ".",
                "code_dir": "code",
                "data_dir": "data",
                "processed_data_dir": "data/processed",
                "logs_dir": "data/logs"
            }
        }
        
        # Should not raise
        validate_paths_config(config)
        
    def test_missing_paths_key(self):
        """Test that missing 'paths' key raises error."""
        config = {}
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)
            
    def test_paths_not_dict(self):
        """Test that non-dict paths raises error."""
        config = {"paths": "not_a_dict"}
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)
            
    def test_empty_paths(self):
        """Test that empty paths dict raises error."""
        config = {"paths": {}}
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)
            
    def test_missing_required_path(self):
        """Test that missing required path key raises error."""
        config = {
            "paths": {
                "root": ".",
                "code_dir": "code"
                # Missing data_dir, processed_data_dir, logs_dir
            }
        }
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)
            
    def test_empty_path_value(self):
        """Test that empty path value raises error."""
        config = {
            "paths": {
                "root": "",
                "code_dir": "code",
                "data_dir": "data",
                "processed_data_dir": "data/processed",
                "logs_dir": "data/logs"
            }
        }
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)
            
    def test_none_path_value(self):
        """Test that None path value raises error."""
        config = {
            "paths": {
                "root": None,
                "code_dir": "code",
                "data_dir": "data",
                "processed_data_dir": "data/processed",
                "logs_dir": "data/logs"
            }
        }
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)
            
    def test_non_string_path_value(self):
        """Test that non-string path value raises error."""
        config = {
            "paths": {
                "root": 123,
                "code_dir": "code",
                "data_dir": "data",
                "processed_data_dir": "data/processed",
                "logs_dir": "data/logs"
            }
        }
        
        with pytest.raises(DataInsufficientError):
            validate_paths_config(config)


class TestVerifyAllKeysExist:
    """Tests for verify_all_keys_exist function."""
    
    def test_valid_section_dict(self):
        """Test verification of a valid dict section."""
        config = {"section": {"key1": "value1", "key2": "value2"}}
        
        result = verify_all_keys_exist(config, "section")
        assert result is True
        
    def test_valid_section_list(self):
        """Test verification of a valid list section."""
        config = {"section": ["item1", "item2"]}
        
        result = verify_all_keys_exist(config, "section")
        assert result is True
        
    def test_missing_section(self):
        """Test that missing section raises error."""
        config = {}
        
        with pytest.raises(DataInsufficientError):
            verify_all_keys_exist(config, "missing_section")
            
    def test_empty_dict_section(self):
        """Test that empty dict section raises error."""
        config = {"section": {}}
        
        with pytest.raises(DataInsufficientError):
            verify_all_keys_exist(config, "section")
            
    def test_empty_list_section(self):
        """Test that empty list section raises error."""
        config = {"section": []}
        
        with pytest.raises(DataInsufficientError):
            verify_all_keys_exist(config, "section")
            
    def test_none_section(self):
        """Test that None section raises error."""
        config = {"section": None}
        
        with pytest.raises(DataInsufficientError):
            verify_all_keys_exist(config, "section")