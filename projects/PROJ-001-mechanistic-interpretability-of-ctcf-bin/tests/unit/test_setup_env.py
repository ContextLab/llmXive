import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

import yaml

# Import the module under test
from code.setup_env import (
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


class TestSetupEnv(TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_project_root = Path(self.temp_dir.name)
        
        # Create necessary subdirectories
        (self.test_project_root / "data" / "raw").mkdir(parents=True)
        (self.test_project_root / "data" / "processed").mkdir(parents=True)
        (self.test_project_root / "config").mkdir(parents=True)
        
        # Patch PROJECT_ROOT for testing
        self.original_root = PROJECT_ROOT
        self.patcher = patch("code.setup_env.PROJECT_ROOT", self.test_project_root)
        self.patcher.start()
        
        # Also patch CONFIG_PATH and MANIFEST_PATH
        self.patcher_config = patch("code.setup_env.CONFIG_PATH", self.test_project_root / "config" / "env_config.yaml")
        self.patcher_config.start()
        self.patcher_manifest = patch("code.setup_env.MANIFEST_PATH", self.test_project_root / "data" / "manifest.json")
        self.patcher_manifest.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.patcher.stop()
        self.patcher_config.stop()
        self.patcher_manifest.stop()
        self.temp_dir.cleanup()

    def test_load_env_config_missing_file(self):
        """Test that load_env_config raises FileNotFoundError for missing file."""
        with self.assertRaises(FileNotFoundError):
            load_env_config()

    def test_load_env_config_valid(self):
        """Test loading a valid configuration file."""
        config_data = {
            "credentials": {"encode_api_key": "test_key_123"},
            "paths": {"raw_data": "data/raw"},
            "settings": {"shannon_entropy_threshold": 0.8}
        }
        
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        loaded = load_env_config()
        self.assertEqual(loaded["credentials"]["encode_api_key"], "test_key_123")
        self.assertEqual(loaded["settings"]["shannon_entropy_threshold"], 0.8)

    def test_validate_manifest_exists_false(self):
        """Test validate_manifest_exists returns False when manifest is missing."""
        self.assertFalse(validate_manifest_exists())

    def test_validate_manifest_exists_true(self):
        """Test validate_manifest_exists returns True when manifest exists."""
        manifest_path = self.test_project_root / "data" / "manifest.json"
        manifest_path.write_text(json.dumps({"test": "data"}))
        self.assertTrue(validate_manifest_exists())

    def test_get_encode_api_key_from_config(self):
        """Test API key retrieval from config file."""
        config_data = {
            "credentials": {"encode_api_key": "config_key_456"}
        }
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        key = get_encode_api_key()
        self.assertEqual(key, "config_key_456")

    def test_get_encode_api_key_from_env(self):
        """Test API key retrieval from environment variable when config is missing."""
        # Create config without API key
        config_data = {"credentials": {}}
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        with patch.dict(os.environ, {"ENCODE_API_KEY": "env_key_789"}):
            key = get_encode_api_key()
            self.assertEqual(key, "env_key_789")

    def test_get_encode_api_key_fallback_secret(self):
        """Test API key retrieval from ENCODE_ACCESS_KEY_ID fallback."""
        config_data = {"credentials": {}}
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        with patch.dict(os.environ, {"ENCODE_ACCESS_KEY_ID": "fallback_key_999"}):
            key = get_encode_api_key()
            self.assertEqual(key, "fallback_key_999")

    def test_get_encode_api_key_missing(self):
        """Test that ValueError is raised when no API key is found."""
        config_data = {"credentials": {}}
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        with self.assertRaises(ValueError):
            get_encode_api_key()

    def test_get_data_paths_defaults(self):
        """Test that default paths are resolved correctly."""
        config_data = {}
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        paths = get_data_paths()
        self.assertIn("raw_data", paths)
        self.assertIn("processed_data", paths)
        self.assertTrue(paths["raw_data"].endswith("data/raw"))
        self.assertTrue(paths["processed_data"].endswith("data/processed"))

    def test_get_data_paths_overrides(self):
        """Test that config paths override defaults."""
        config_data = {
            "paths": {
                "raw_data": "custom/raw",
                "models": "/absolute/path/models"
            }
        }
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        paths = get_data_paths()
        self.assertTrue(paths["raw_data"].endswith("custom/raw"))
        self.assertTrue(paths["models"], "/absolute/path/models")

    def test_ensure_directories_creates_missing(self):
        """Test that ensure_directories creates missing directories."""
        new_dir = self.test_project_root / "data" / "new_folder"
        self.assertFalse(new_dir.exists())
        
        config_data = {"paths": {"new_folder": "data/new_folder"}}
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        # Manually patch get_data_paths to include new_folder for this test
        original_get_paths = get_data_paths
        def mock_get_paths(cfg):
            base = original_get_paths(cfg)
            base["new_folder"] = str(new_dir)
            return base
            
        with patch("code.setup_env.get_data_paths", mock_get_paths):
            ensure_directories()
            
        self.assertTrue(new_dir.exists())

    def test_write_sample_config(self):
        """Test that write_sample_config creates a valid YAML file."""
        output_path = self.test_project_root / "config" / "sample_config.yaml"
        result_path = write_sample_config(output_path)
        
        self.assertEqual(result_path, output_path)
        self.assertTrue(output_path.exists())
        
        with open(output_path, "r") as f:
            loaded = yaml.safe_load(f)
            
        self.assertIn("credentials", loaded)
        self.assertIn("encode_api_key", loaded["credentials"])
        self.assertIn("paths", loaded)
        self.assertIn("settings", loaded)

    def test_main_success(self):
        """Test main() returns 0 on successful validation."""
        # Create a valid config
        config_data = {
            "credentials": {"encode_api_key": "test_key"},
            "paths": {}
        }
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        # Create manifest
        manifest_path = self.test_project_root / "data" / "manifest.json"
        manifest_path.write_text(json.dumps({"test": "data"}))
        
        # Mock sys.argv
        with patch("sys.argv", ["setup_env.py", "--validate"]):
            # Import main here to use patched argv
            import code.setup_env as setup_env_module
            # Reload to pick up patches if needed, but argv is global
            result = setup_env_module.main()
            
        self.assertEqual(result, 0)

    def test_main_missing_manifest(self):
        """Test main() returns 1 when manifest is missing."""
        # Create valid config but no manifest
        config_data = {"credentials": {"encode_api_key": "test_key"}}
        config_path = self.test_project_root / "config" / "env_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
            
        with patch("sys.argv", ["setup_env.py", "--validate"]):
            import code.setup_env as setup_env_module
            result = setup_env_module.main()
            
        self.assertEqual(result, 1)