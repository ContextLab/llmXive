import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the module under test
from setup_env import (
    load_env_config,
    validate_manifest_exists,
    get_encode_api_key,
    get_data_paths,
    ensure_directories,
    write_sample_config,
    PROJECT_ROOT,
    CONFIG_PATH,
    MANIFEST_PATH,
)

class TestLoadEnvConfig:
    def test_load_from_file(self, tmp_path):
        """Test loading config from an existing YAML file."""
        config_data = {
            "encode_api_key": "test_key_123",
            "data_paths": {"raw": "/tmp/raw"},
        }
        config_file = tmp_path / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        result = load_env_config(config_file)
        assert result["encode_api_key"] == "test_key_123"
        assert result["data_paths"]["raw"] == "/tmp/raw"

    def test_load_default_if_missing(self, tmp_path):
        """Test that default structure is returned if file is missing."""
        missing_file = tmp_path / "nonexistent.yaml"
        result = load_env_config(missing_file)
        assert "encode_api_key" in result
        assert "data_paths" in result
        assert result["encode_api_key"] == ""

class TestValidateManifestExists:
    def test_manifest_exists(self, tmp_path):
        """Test validation when manifest exists."""
        manifest_file = tmp_path / "manifest.json"
        manifest_file.write_text("{}")
        assert validate_manifest_exists(manifest_file) is True

    def test_manifest_missing(self, tmp_path):
        """Test validation when manifest is missing."""
        missing_file = tmp_path / "missing_manifest.json"
        with pytest.raises(FileNotFoundError):
            validate_manifest_exists(missing_file)

class TestGetEncodeApiKey:
    def test_from_config(self):
        """Test retrieving API key from config dict."""
        config = {"encode_api_key": "key_from_config"}
        assert get_encode_api_key(config) == "key_from_config"

    def test_from_env(self, monkeypatch):
        """Test retrieving API key from environment variable."""
        monkeypatch.setenv("ENCODE_API_KEY", "key_from_env")
        config = {}  # Empty config
        assert get_encode_api_key(config) == "key_from_env"

    def test_missing_raises(self):
        """Test that missing API key raises ValueError."""
        config = {}
        os.environ.pop("ENCODE_API_KEY", None)
        with pytest.raises(ValueError, match="ENCODE API key not found"):
            get_encode_api_key(config)

class TestGetDataPaths:
    def test_from_config(self):
        """Test retrieving paths from config."""
        config = {
            "data_paths": {
                "raw": "/custom/raw",
                "processed": "/custom/processed",
            }
        }
        paths = get_data_paths(config)
        assert paths["raw"] == "/custom/raw"
        assert paths["processed"] == "/custom/processed"
        # Check defaults for missing keys
        assert "models" in paths

    def test_defaults_when_empty(self):
        """Test defaults when config is empty."""
        config = {}
        paths = get_data_paths(config)
        assert "raw" in paths
        assert "processed" in paths

class TestEnsureDirectories:
    def test_creates_directories(self, tmp_path):
        """Test that ensure_directories creates the specified paths."""
        paths = {
            "raw": str(tmp_path / "raw"),
            "processed": str(tmp_path / "processed"),
        }
        ensure_directories(paths)
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "processed").exists()

class TestWriteSampleConfig:
    def test_creates_sample_config(self, tmp_path):
        """Test that write_sample_config creates a valid YAML file."""
        output_file = tmp_path / "sample_config.yaml"
        result_path = write_sample_config(output_file)
        
        assert result_path.exists()
        with open(result_path, "r") as f:
            data = yaml.safe_load(f)
        
        assert "encode_api_key" in data
        assert "YOUR_ENCODE_API_KEY_HERE" in data["encode_api_key"]
        assert "data_paths" in data
        assert "notes" in data
