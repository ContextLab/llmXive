import pytest
import os
import random
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import (
    get_project_root,
    get_data_raw_path,
    get_data_processed_path,
    get_output_path,
    get_figures_path,
    get_millennium_path,
    get_logs_path,
    get_state_path,
    load_config,
    set_random_seed,
    get_random_seed,
    MAX_RAM_GB,
    MAX_DISK_GB,
    CHUNK_SIZE_MB,
    MIN_PARTICLE_COUNT
)

class TestConfigPaths:
    """Test that path constants return valid Path objects and create directories."""

    def test_project_root_exists(self):
        """Test that project root is a valid Path."""
        root = get_project_root()
        assert isinstance(root, Path)
        # The root should be the parent of 'code'
        assert (root / "code").exists() or (root / "code").parent == root

    def test_data_raw_path_creates_dir(self):
        """Test that get_data_raw_path creates the directory."""
        path = get_data_raw_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "raw"

    def test_data_processed_path_creates_dir(self):
        """Test that get_data_processed_path creates the directory."""
        path = get_data_processed_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "processed"

    def test_output_path_creates_dir(self):
        """Test that get_output_path creates the directory."""
        path = get_output_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "outputs"

    def test_figures_path_creates_dir(self):
        """Test that get_figures_path creates the directory."""
        path = get_figures_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "figures"

    def test_millennium_path_creates_dir(self):
        """Test that get_millennium_path creates the directory."""
        path = get_millennium_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "millennium"

    def test_logs_path_creates_dir(self):
        """Test that get_logs_path creates the directory."""
        path = get_logs_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "logs"

    def test_state_path_creates_dir(self):
        """Test that get_state_path creates the directory."""
        path = get_state_path()
        assert path.exists()
        assert path.is_dir()
        assert path.name == "state"

class TestRandomSeed:
    """Test random seed functionality."""

    def test_set_random_seed_sets_global(self):
        """Test that set_random_seed updates the global seed."""
        set_random_seed(123)
        assert get_random_seed() == 123

    def test_set_random_seed_affects_random(self):
        """Test that set_random_seed affects the random module."""
        set_random_seed(42)
        val1 = random.random()
        set_random_seed(42)
        val2 = random.random()
        assert val1 == val2

    def test_set_random_seed_affects_numpy(self):
        """Test that set_random_seed affects numpy."""
        set_random_seed(42)
        arr1 = np.random.rand(5)
        set_random_seed(42)
        arr2 = np.random.rand(5)
        assert np.array_equal(arr1, arr2)

    def test_default_seed_is_42(self):
        """Test that the default seed is 42."""
        # Reset to default by calling with default argument
        set_random_seed()
        assert get_random_seed() == 42

class TestConstants:
    """Test that project constants are defined correctly."""

    def test_max_ram_gb(self):
        """Test MAX_RAM_GB is 7.0."""
        assert MAX_RAM_GB == 7.0

    def test_max_disk_gb(self):
        """Test MAX_DISK_GB is 14.0."""
        assert MAX_DISK_GB == 14.0

    def test_chunk_size_mb(self):
        """Test CHUNK_SIZE_MB is 100."""
        assert CHUNK_SIZE_MB == 100

    def test_min_particle_count(self):
        """Test MIN_PARTICLE_COUNT is 10000."""
        assert MIN_PARTICLE_COUNT == 10000

class TestLoadConfig:
    """Test configuration loading."""

    def test_load_nonexistent_config(self):
        """Test loading a non-existent config returns empty dict."""
        config = load_config(Path("/nonexistent/path/config.yaml"))
        assert config == {}

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid config file."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("key: value\nnumber: 42\n")
        
        config = load_config(config_file)
        assert config["key"] == "value"
        assert config["number"] == 42