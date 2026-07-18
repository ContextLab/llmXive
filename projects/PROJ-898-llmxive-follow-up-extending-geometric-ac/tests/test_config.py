"""
Tests for the configuration loader module.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path

from code.config import (
    ExperimentConfig,
    create_default_config_file,
    load_config,
    save_config,
)


class TestExperimentConfig(unittest.TestCase):
    """Test cases for ExperimentConfig dataclass."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = ExperimentConfig()
        self.assertEqual(config.topology_counts, 50)
        self.assertEqual(config.material_types, ["soft_rope", "cloth"])
        self.assertEqual(config.timeout_limit_seconds, 300.0)
        self.assertEqual(config.max_steps_per_trial, 100)
        self.assertEqual(config.random_seed, 42)
        self.assertEqual(config.batch_size, 1)
        self.assertEqual(config.output_dir, "data/generated")
        self.assertEqual(config.baseline_metadata_path, "data/raw/gam_baseline_metadata.json")
        self.assertFalse(config.enable_profiling)
        self.assertTrue(config.cpu_only)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ExperimentConfig(topology_counts=100, timeout_limit_seconds=600.0)
        config_dict = config.to_dict()
        self.assertEqual(config_dict["topology_counts"], 100)
        self.assertEqual(config_dict["timeout_limit_seconds"], 600.0)
        self.assertIn("material_types", config_dict)

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "topology_counts": 75,
            "material_types": ["elastic_band"],
            "timeout_limit_seconds": 450.0,
            "max_steps_per_trial": 200,
            "random_seed": 123,
            "batch_size": 4,
            "output_dir": "data/test_output",
            "baseline_metadata_path": "data/test_baseline.json",
            "enable_profiling": True,
            "cpu_only": False,
        }
        config = ExperimentConfig.from_dict(data)
        self.assertEqual(config.topology_counts, 75)
        self.assertEqual(config.material_types, ["elastic_band"])
        self.assertEqual(config.timeout_limit_seconds, 450.0)
        self.assertEqual(config.max_steps_per_trial, 200)
        self.assertEqual(config.random_seed, 123)
        self.assertEqual(config.batch_size, 4)
        self.assertEqual(config.output_dir, "data/test_output")
        self.assertEqual(config.baseline_metadata_path, "data/test_baseline.json")
        self.assertTrue(config.enable_profiling)
        self.assertFalse(config.cpu_only)

    def test_round_trip(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = ExperimentConfig(topology_counts=99, timeout_limit_seconds=999.0)
        config_dict = original.to_dict()
        restored = ExperimentConfig.from_dict(config_dict)
        self.assertEqual(original.topology_counts, restored.topology_counts)
        self.assertEqual(original.timeout_limit_seconds, restored.timeout_limit_seconds)
        self.assertEqual(original.material_types, restored.material_types)


class TestConfigIO(unittest.TestCase):
    """Test cases for config file I/O operations."""

    def setUp(self):
        """Set up temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_save_and_load_config(self):
        """Test saving and loading a configuration file."""
        original = ExperimentConfig(
            topology_counts=200,
            material_types=["rope", "cloth", "gel"],
            timeout_limit_seconds=120.5,
        )
        save_config(original, self.config_path)
        self.assertTrue(os.path.exists(self.config_path))

        loaded = load_config(self.config_path)
        self.assertEqual(loaded.topology_counts, 200)
        self.assertEqual(loaded.material_types, ["rope", "cloth", "gel"])
        self.assertEqual(loaded.timeout_limit_seconds, 120.5)

    def test_load_nonexistent_file(self):
        """Test that loading a nonexistent file raises an error."""
        with self.assertRaises(FileNotFoundError):
            load_config("nonexistent/path/config.json")

    def test_create_default_config_file(self):
        """Test creating a default configuration file."""
        default_path = os.path.join(self.temp_dir.name, "default_config.json")
        create_default_config_file(default_path)
        self.assertTrue(os.path.exists(default_path))

        with open(default_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["topology_counts"], 50)
        self.assertEqual(data["timeout_limit_seconds"], 300.0)

    def test_load_default_config(self):
        """Test loading config with no path returns defaults."""
        config = load_config()
        self.assertEqual(config.topology_counts, 50)
        self.assertEqual(config.timeout_limit_seconds, 300.0)

    def test_invalid_json(self):
        """Test that invalid JSON raises an error."""
        invalid_path = os.path.join(self.temp_dir.name, "invalid.json")
        with open(invalid_path, "w") as f:
            f.write("{ invalid json }")

        with self.assertRaises(json.JSONDecodeError):
            load_config(invalid_path)


if __name__ == "__main__":
    unittest.main()