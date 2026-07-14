"""
Unit tests for code/utils/config.py

Verifies:
1. Paths resolve correctly relative to project root.
2. Hardcoded seeds are enforced even if YAML suggests otherwise.
3. Default hyperparameters are returned if config.yaml is missing.
4. YAML overrides are applied correctly for non-seed values.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.utils import config

class TestConfigSeeds:
    def test_hardcoded_seeds_unchanged(self):
        """Ensure seeds are the specific hardcoded values."""
        assert config.RANDOM_SEED == 42
        assert config.LIGHTGBM_SEED == 42
        assert config.NUMPY_SEED == 42

    def test_yaml_seeds_ignored(self):
        """
        Verify that even if config.yaml contains random_state,
        the loaded hyperparameters use the hardcoded seed.
        """
        yaml_content = """
        model:
          random_state: 9999
          n_estimators: 100
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            loaded = config.load_hyperparameters(temp_path)
            # The seed should be the hardcoded one, not 9999
            assert loaded['model']['random_state'] == config.LIGHTGBM_SEED
            assert loaded['model']['random_state'] != 9999
        finally:
            os.unlink(temp_path)

class TestConfigPaths:
    def test_project_root_is_parent_of_code(self):
        """Verify project root is correctly identified."""
        assert config.PROJECT_ROOT.name == "PROJ-091-predicting-molecular-polarity-from-smile" or \
               config.PROJECT_ROOT.name == "code".replace("code", "root") # Fallback check
        # More robust check: code/utils/config.py is 3 levels deep
        assert (config.PROJECT_ROOT / "code").exists()
        assert (config.PROJECT_ROOT / "data").exists()

    def test_data_dirs_exist(self):
        """Verify data directories are created or exist."""
        assert config.DATA_RAW_DIR.exists()
        assert config.DATA_PROCESSED_DIR.exists()
        assert config.DATA_ANALYSIS_DIR.exists()

class TestConfigLoading:
    def test_missing_yaml_returns_defaults(self):
        """If config.yaml is missing, defaults should be returned."""
        # Temporarily hide the real config if it exists in the repo
        # We test against a non-existent path
        loaded = config.load_hyperparameters(Path("/nonexistent/path.yaml"))
        assert loaded == config.DEFAULT_HYPERPARAMETERS

    def test_yaml_overrides_defaults(self):
        """Verify non-seed values are overridden by YAML."""
        yaml_content = """
        model:
          n_estimators: 5000
          learning_rate: 0.001
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = Path(f.name)

        try:
            loaded = config.load_hyperparameters(temp_path)
            assert loaded['model']['n_estimators'] == 5000
            assert loaded['model']['learning_rate'] == 0.001
            # But seed remains hardcoded
            assert loaded['model']['random_state'] == config.LIGHTGBM_SEED
        finally:
            os.unlink(temp_path)

class TestConfigSummary:
    def test_get_config_summary_runs(self):
        """Ensure the summary function runs without error."""
        summary = config.get_config_summary()
        assert isinstance(summary, str)
        assert "Project Root" in summary
        assert "Hardcoded Seeds" in summary