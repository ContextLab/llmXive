"""
Tests for config/settings.py
"""
import pytest
import json
from pathlib import Path
from code.config.settings import (
    get_config,
    get_target_repos,
    get_paths,
    ensure_directories,
    PROJECT_ROOT,
    RANDOM_SEED,
    HYPERPARAMETERS,
    RUNTIME_LIMIT_SECONDS
)

class TestSettings:
    def test_get_config_returns_dict(self):
        config = get_config()
        assert isinstance(config, dict)
        assert "random_seed" in config
        assert "hyperparameters" in config
        assert "paths" in config
        assert "target_repos" in config

    def test_random_seed_defined(self):
        assert isinstance(RANDOM_SEED, int)
        assert RANDOM_SEED > 0

    def test_runtime_limit_is_six_hours(self):
        # 6 hours * 60 minutes * 60 seconds
        assert RUNTIME_LIMIT_SECONDS == 21600

    def test_hyperparameters_contain_expected_keys(self):
        required_keys = [
            "max_context_tokens",
            "similarity_threshold",
            "jaccard_min_overlap",
            "max_latency_seconds"
        ]
        for key in required_keys:
            assert key in HYPERPARAMETERS

    def test_get_target_repos_returns_list(self):
        repos = get_target_repos()
        assert isinstance(repos, list)
        assert len(repos) > 0
        # Check format (owner/repo)
        for repo in repos:
            assert "/" in repo

    def test_get_paths_returns_paths(self):
        paths = get_paths()
        assert isinstance(paths, dict)
        assert "data" in paths
        assert "results" in paths
        assert "logs" in paths

    def test_project_root_is_path_object(self):
        assert isinstance(PROJECT_ROOT, Path)

    def test_config_serializable(self):
        config = get_config()
        # Should not raise
        json_str = json.dumps(config)
        assert len(json_str) > 0

    def test_ensure_directories_creates_folders(self, tmp_path, monkeypatch):
        """
        Test that ensure_directories actually creates directories.
        We patch PROJECT_ROOT to a temp directory for this test.
        """
        import code.config.settings as settings_module
        
        # Save original
        original_root = settings_module.PROJECT_ROOT
        
        # Create a temp root
        temp_root = tmp_path / "test_project"
        
        # Monkeypatch the module
        settings_module.PROJECT_ROOT = temp_root
        # Re-evaluate PATHS based on new root would be complex, 
        # so we just test the logic by calling ensure_directories on a known structure
        
        # Instead, let's just verify the function exists and doesn't crash
        # by patching the internal PATHS to point to tmp_path
        original_paths = settings_module.PATHS
        
        settings_module.PATHS = {
            "test_dir": temp_root / "new_dir",
            "nested": {
                "sub_dir": temp_root / "nested" / "sub"
            }
        }
        
        try:
            settings_module.ensure_directories()
            assert (temp_root / "new_dir").exists()
            assert (temp_root / "nested" / "sub").exists()
        finally:
            # Restore
            settings_module.PROJECT_ROOT = original_root
            settings_module.PATHS = original_paths
