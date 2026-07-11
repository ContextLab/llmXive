"""
Tests for the environment configuration management module (T004).
"""

import os
import tempfile
from pathlib import Path
import pytest

# Add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from config.settings import (
    Settings,
    get_settings,
    reload_settings,
    get_database_path,
    get_data_dir,
    get_model_path,
    get_api_key,
    validate_api_keys,
    DatabaseConfig,
    DatasetConfig,
    ModelConfig,
    EncryptionConfig,
    ExperimentConfig
)

class TestSettingsInitialization:
    def test_settings_creates_directories(self, tmp_path):
        """Test that Settings creates necessary directories."""
        # Mock project root to tmp_path
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            # Create a mock settings instance with tmp_path as root
            settings = Settings(project_root=tmp_path)
            assert settings.data_dir.exists()
            assert settings.logs_dir.exists()
            assert settings.models_dir.exists()
            assert settings.code_dir.exists()
        finally:
            os.chdir(original_cwd)

    def test_database_config_defaults(self):
        """Test that database config defaults correctly."""
        settings = Settings()
        assert settings.database.dialect == "sqlite"
        assert settings.database.path.suffix == ".db"

    def test_experiment_config_from_env(self, monkeypatch):
        """Test that experiment config reads from environment variables."""
        monkeypatch.setenv("EXPERIMENT_SEED", "12345")
        monkeypatch.setenv("EXPERIMENT_TIMEOUT", "600")
        
        # Reload settings to pick up new env vars
        settings = reload_settings()
        assert settings.experiment.seed == 12345
        assert settings.experiment.timeout_seconds == 600

    def test_encryption_config_from_env(self, monkeypatch):
        """Test that encryption key is read from environment."""
        test_key = "test_encryption_key_32_bytes_long!!"
        monkeypatch.setenv("CODEX_ENCRYPTION_KEY", test_key)
        
        settings = reload_settings()
        assert settings.encryption.key == test_key

    def test_api_keys_from_env(self, monkeypatch):
        """Test that API keys are read from environment."""
        monkeypatch.setenv("HF_TOKEN", "hf_test_token")
        monkeypatch.setenv("GITHUB_TOKEN", "gh_test_token")
        
        settings = reload_settings()
        assert settings.api_keys["HF_TOKEN"] == "hf_test_token"
        assert settings.api_keys["GITHUB_TOKEN"] == "gh_test_token"

class TestSettingsAccessors:
    def test_get_settings_singleton(self):
        """Test that get_settings returns a singleton."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_get_database_path(self):
        """Test that get_database_path returns the correct path."""
        settings = get_settings()
        assert get_database_path() == settings.database.path

    def test_get_data_dir(self):
        """Test that get_data_dir returns the correct directory."""
        settings = get_settings()
        assert get_data_dir() == settings.data_dir

    def test_get_model_path(self):
        """Test model path retrieval."""
        settings = get_settings()
        # Test with non-existent models
        assert get_model_path("starcoder") is None
        assert get_model_path("jacotext") is None
        assert get_model_path("unknown") is None

    def test_get_api_key(self):
        """Test API key retrieval."""
        settings = get_settings()
        assert get_api_key("HF_TOKEN") == settings.api_keys.get("HF_TOKEN")
        assert get_api_key("NON_EXISTENT_KEY") is None

    def test_validate_api_keys_success(self, monkeypatch):
        """Test validation when keys are present."""
        monkeypatch.setenv("HF_TOKEN", "test")
        monkeypatch.setenv("GITHUB_TOKEN", "test")
        settings = reload_settings()
        assert validate_api_keys(["HF_TOKEN", "GITHUB_TOKEN"]) is True

    def test_validate_api_keys_failure(self, monkeypatch):
        """Test validation when keys are missing."""
        monkeypatch.delenv("HF_TOKEN", raising=False)
        settings = reload_settings()
        assert validate_api_keys(["HF_TOKEN"]) is False

class TestConfigDataclasses:
    def test_database_config_path_conversion(self):
        """Test that DatabaseConfig converts string paths to Path objects."""
        db = DatabaseConfig(path="relative/path/to/db.sqlite")
        assert isinstance(db.path, Path)

    def test_dataset_config_creates_dirs(self, tmp_path):
        """Test that DatasetConfig creates directories."""
        ds = DatasetConfig(
            humaneval_dir=tmp_path / "humaneval",
            codeforces_dir=tmp_path / "codeforces"
        )
        assert ds.humaneval_dir.exists()
        assert ds.codeforces_dir.exists()

    def test_model_config_defaults(self):
        """Test ModelConfig defaults."""
        mc = ModelConfig()
        assert mc.cpu_only is True
        assert mc.max_model_size_gb == 1.0

    def test_encryption_config_default(self):
        """Test EncryptionConfig defaults."""
        ec = EncryptionConfig()
        assert ec.algorithm == "AES-256-GCM"

    def test_experiment_config_defaults(self):
        """Test ExperimentConfig defaults."""
        ec = ExperimentConfig()
        assert ec.seed == 42
        assert ec.timeout_seconds == 300
        assert ec.min_solution_time_seconds == 300
        assert ec.fast_completion_threshold_seconds == 30
        assert ec.participant_experience_filter_years == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
