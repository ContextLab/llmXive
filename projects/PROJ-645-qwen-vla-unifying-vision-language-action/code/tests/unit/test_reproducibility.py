import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import yaml

from src.utils.reproducibility import (
    generate_seeds,
    save_seeds,
    load_seeds,
    get_git_commit_hash,
    get_python_version,
    get_package_versions,
    collect_hyperparameters,
    log_reproducibility_manifest,
    run_reproducibility_pipeline,
    NUM_SEEDS,
    SEEDS_FILE,
    MANIFEST_FILE
)

class TestReproducibility:
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory for testing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        # Change CWD to tmp_path to simulate project root
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        yield tmp_path
        os.chdir(original_cwd)

    def test_generate_seeds_count(self):
        """Verify that generate_seeds returns exactly 5 seeds."""
        seeds = generate_seeds()
        assert len(seeds) == NUM_SEEDS
        assert all(isinstance(s, int) for s in seeds)
        # Check range
        assert all(0 <= s <= 2**32 - 1 for s in seeds)

    def test_generate_seeds_deterministic(self):
        """Verify that seeds are deterministic given the same MASTER_SEED."""
        with patch.dict(os.environ, {"MASTER_SEED": "12345"}):
            seeds1 = generate_seeds()
            seeds2 = generate_seeds()
        assert seeds1 == seeds2

    def test_save_and_load_seeds(self, temp_data_dir):
        """Test saving and loading seeds to/from JSON."""
        test_seeds = [1, 2, 3, 4, 5]
        output_path = str(temp_data_dir / "test_seeds.json")
        
        save_seeds(test_seeds, output_path)
        
        assert os.path.exists(output_path)
        
        loaded_seeds = load_seeds(output_path)
        assert loaded_seeds == test_seeds

    def test_save_seeds_creates_directory(self, tmp_path):
        """Test that save_seeds creates parent directories if they don't exist."""
        nested_path = str(tmp_path / "deep" / "nested" / "data" / "seeds.json")
        test_seeds = [10, 20, 30, 40, 50]
        
        save_seeds(test_seeds, nested_path)
        
        assert os.path.exists(nested_path)

    def test_load_seeds_missing_file(self, temp_data_dir):
        """Test that load_seeds raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_seeds(str(temp_data_dir / "nonexistent.json"))

    def test_get_python_version(self):
        """Test that get_python_version returns a valid version string."""
        version = get_python_version()
        assert isinstance(version, str)
        assert len(version.split(".")) >= 2

    def test_get_package_versions(self):
        """Test that get_package_versions returns a dict with expected keys."""
        versions = get_package_versions()
        assert isinstance(versions, dict)
        assert "torch" in versions
        assert "psutil" in versions

    def test_collect_hyperparameters(self):
        """Test hyperparameter collection with defaults and overrides."""
        # Test defaults
        defaults = collect_hyperparameters()
        assert defaults["batch_size"] == 32
        
        # Test overrides
        custom = {"batch_size": 64, "new_param": "value"}
        merged = collect_hyperparameters(custom)
        assert merged["batch_size"] == 64
        assert merged["new_param"] == "value"

    def test_log_reproducibility_manifest(self, temp_data_dir):
        """Test writing the manifest file."""
        seeds = [1, 2, 3, 4, 5]
        hyperparams = {"lr": 0.001}
        output_path = str(temp_data_dir / "test_manifest.yaml")
        
        log_reproducibility_manifest(seeds, hyperparams, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, "r") as f:
            data = yaml.safe_load(f)
        
        assert "seeds" in data
        assert data["seeds"]["values"] == seeds
        assert "hyperparameters" in data
        assert "git_commit" in data
        assert "packages" in data

    def test_run_reproducibility_pipeline(self, temp_data_dir):
        """Test the full pipeline execution."""
        # Mock subprocess to avoid git errors in test environment
        with patch("src.utils.reproducibility.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="abc123")
            
            result = run_reproducibility_pipeline()
            
            assert "seeds_file" in result
            assert "manifest_file" in result
            assert os.path.exists(result["seeds_file"])
            assert os.path.exists(result["manifest_file"])

    def test_seed_values_in_range(self):
        """Verify all generated seeds are within valid 32-bit integer range."""
        seeds = generate_seeds()
        for seed in seeds:
            assert 0 <= seed <= 2**32 - 1, f"Seed {seed} out of range"