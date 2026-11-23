import pytest
import json
import tempfile
from pathlib import Path
import os

# Import the module under test
from config_env import (
    EnvConfig,
    get_env_config,
    reset_env_config,
    get_data_path,
    get_datasets_path,
    get_annotations_path,
    get_results_path,
    verify_dataset,
    register_artifact,
    ensure_env_paths_exist,
    get_env_config_summary
)

class TestEnvConfig:
    """Unit tests for environment configuration management."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def env_config(self, temp_dir):
        """Create an EnvConfig instance for testing."""
        return EnvConfig(temp_dir)

    def test_initialization(self, temp_dir):
        """Test that EnvConfig initializes with correct paths."""
        cfg = EnvConfig(temp_dir)
        assert cfg.root == Path(temp_dir).resolve()
        assert cfg.datasets_dir == Path(temp_dir) / "data" / "datasets"
        assert cfg.annotations_dir == Path(temp_dir) / "data" / "annotations"
        assert cfg.results_dir == Path(temp_dir) / "data" / "results"
        assert cfg.artifact_hashes == {}

    def test_ensure_dirs(self, env_config):
        """Test that ensure_dirs creates all required directories."""
        env_config.ensure_dirs()
        assert env_config.datasets_dir.exists()
        assert env_config.annotations_dir.exists()
        assert env_config.results_dir.exists()

    def test_register_artifact(self, env_config, temp_dir):
        """Test artifact registration and hash computation."""
        # Create a test file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Register the artifact
        hash_value = env_config.register_artifact("test_file", str(test_file))
        
        # Verify hash was computed and stored
        assert hash_value != ""
        assert len(hash_value) == 64  # SHA-256 hex length
        assert "test_file" in env_config.artifact_hashes
        assert env_config.artifact_hashes["test_file"] == hash_value

    def test_verify_artifact_valid(self, env_config, temp_dir):
        """Test verifying a valid artifact."""
        # Create and register a test file
        test_file = Path(temp_dir) / "valid.txt"
        test_file.write_text("Valid content")
        env_config.register_artifact("valid_file", str(test_file))
        
        # Verify it
        assert env_config.verify_artifact("valid_file") is True

    def test_verify_artifact_missing(self, env_config):
        """Test verifying a missing artifact."""
        assert env_config.verify_artifact("nonexistent") is False

    def test_save_and_load_hashes(self, env_config, temp_dir):
        """Test saving and loading artifact hashes."""
        # Create and register a test file
        test_file = Path(temp_dir) / "persist.txt"
        test_file.write_text("Persistent")
        env_config.register_artifact("persist_file", str(test_file))
        
        # Save hashes
        env_config.save_hashes()
        
        # Verify hash file exists
        hash_file = env_config.root / "data" / ".artifact_hashes.json"
        assert hash_file.exists()
        
        # Load hashes into a new instance
        new_config = EnvConfig(temp_dir)
        new_config.load_hashes()
        
        # Verify hashes were loaded
        assert "persist_file" in new_config.artifact_hashes

    def test_compute_file_hash(self, env_config, temp_dir):
        """Test file hash computation."""
        test_file = Path(temp_dir) / "hash_test.txt"
        test_file.write_text("Test content")
        
        hash1 = env_config._compute_file_hash(test_file)
        hash2 = env_config._compute_file_hash(test_file)
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64

class TestGlobalFunctions:
    """Unit tests for global configuration functions."""

    @pytest.fixture
    def reset_config(self):
        """Reset global config before and after test."""
        reset_env_config()
        yield
        reset_env_config()

    def test_get_env_config_creates_instance(self, reset_config, temp_dir):
        """Test that get_env_config creates an instance if none exists."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        config = get_env_config()
        assert isinstance(config, EnvConfig)
        del os.environ["LLMXIVE_ROOT"]

    def test_get_data_path(self, reset_config, temp_dir):
        """Test get_data_path returns correct path."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        path = get_data_path()
        assert path == Path(temp_dir) / "data"
        del os.environ["LLMXIVE_ROOT"]

    def test_get_datasets_path(self, reset_config, temp_dir):
        """Test get_datasets_path returns correct path."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        path = get_datasets_path()
        assert path == Path(temp_dir) / "data" / "datasets"
        del os.environ["LLMXIVE_ROOT"]

    def test_get_annotations_path(self, reset_config, temp_dir):
        """Test get_annotations_path returns correct path."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        path = get_annotations_path()
        assert path == Path(temp_dir) / "data" / "annotations"
        del os.environ["LLMXIVE_ROOT"]

    def test_get_results_path(self, reset_config, temp_dir):
        """Test get_results_path returns correct path."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        path = get_results_path()
        assert path == Path(temp_dir) / "data" / "results"
        del os.environ["LLMXIVE_ROOT"]

    def test_ensure_env_paths_exist(self, reset_config, temp_dir):
        """Test ensure_env_paths_exist creates directories."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        ensure_env_paths_exist()
        
        config = get_env_config()
        assert config.datasets_dir.exists()
        assert config.annotations_dir.exists()
        assert config.results_dir.exists()
        del os.environ["LLMXIVE_ROOT"]

    def test_get_env_config_summary(self, reset_config, temp_dir):
        """Test get_env_config_summary returns expected keys."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        summary = get_env_config_summary()
        
        assert "root" in summary
        assert "datasets_dir" in summary
        assert "annotations_dir" in summary
        assert "results_dir" in summary
        assert "registered_artifacts" in summary
        assert "mode" in summary
        del os.environ["LLMXIVE_ROOT"]

    def test_register_artifact_global(self, reset_config, temp_dir):
        """Test global register_artifact function."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        
        test_file = Path(temp_dir) / "global_test.txt"
        test_file.write_text("Global test")
        
        hash_val = register_artifact("global_test", str(test_file))
        assert hash_val != ""
        del os.environ["LLMXIVE_ROOT"]

    def test_verify_dataset_global(self, reset_config, temp_dir):
        """Test global verify_dataset function."""
        os.environ["LLMXIVE_ROOT"] = temp_dir
        
        test_file = Path(temp_dir) / "verify_test.txt"
        test_file.write_text("Verify test")
        
        register_artifact("verify_test", str(test_file))
        
        assert verify_dataset("verify_test") is True
        del os.environ["LLMXIVE_ROOT"]
