"""
Tests for the base configuration loader in code/__init__.py
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import from the package root
from code import load_config, get_path, get_project_root, get_config_path


class TestLoadConfig:
    def test_load_config_default_missing_file_returns_minimal(self):
        """Test that loading a missing config returns a minimal default dict."""
        # Ensure the default path doesn't exist for this test
        default_path = get_config_path()
        # We don't delete the real file if it exists, we just test the logic
        # by passing a non-existent path explicitly
        result = load_config(Path("/nonexistent/path/config.yaml"))
        
        assert isinstance(result, dict)
        assert "project_id" in result
        assert "paths" in result
        assert result["project_id"] == "PROJ-530-neural-correlates-of-error-monitoring-du"

    def test_load_config_valid_file(self):
        """Test loading a valid YAML config file."""
        test_data = {
            "project_id": "TEST-001",
            "paths": {
                "raw_data": "/some/path"
            },
            "settings": {
                "random_seed": 123
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            result = load_config(temp_path)
            assert result["project_id"] == "TEST-001"
            assert result["paths"]["raw_data"] == "/some/path"
            assert result["settings"]["random_seed"] == 123
        finally:
            os.unlink(temp_path)

    def test_load_config_invalid_yaml_raises(self):
        """Test that invalid YAML raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = Path(f.name)

        try:
            with pytest.raises(yaml.YAMLError):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)


class TestGetPath:
    def test_get_path_valid_key(self):
        """Test retrieving a valid path key."""
        config = {
            "paths": {
                "raw_data": "/absolute/path/to/raw"
            }
        }
        result = get_path("paths.raw_data", config)
        assert result == Path("/absolute/path/to/raw")

    def test_get_path_relative_path_resolves(self):
        """Test that relative paths in config are resolved against project root."""
        # Mock a config with a relative path string
        config = {
            "paths": {
                "raw_data": "data/raw"
            }
        }
        result = get_path("paths.raw_data", config)
        # Should be absolute now
        assert result.is_absolute()
        assert result.name == "raw"
        assert result.parent.name == "data"

    def test_get_path_missing_key_raises(self):
        """Test that a missing key raises KeyError."""
        config = {"paths": {}}
        with pytest.raises(KeyError):
            get_path("paths.missing_key", config)


class TestGetProjectRoot:
    def test_root_is_absolute(self):
        """Test that project root is an absolute path."""
        root = get_project_root()
        assert root.is_absolute()
        assert root.name == "PROJ-530-neural-correlates-of-error-monitoring-du"
