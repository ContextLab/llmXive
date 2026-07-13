"""
Unit tests for the config migration script.
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import pytest

# Add the project root to the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.utils.migrate_config import migrate_config, load_yaml, save_yaml, KEYS_TO_MIGRATE

class TestMigrateConfig:
    def test_migrate_existing_keys(self, tmp_path):
        """Test migration of existing keys from config to state."""
        # Setup temporary paths
        config_path = tmp_path / "code" / "config.yaml"
        state_path = tmp_path / "state" / "projects" / "PROJ-024-test.yaml"
        
        # Create directory structure
        config_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create test config with keys to migrate
        test_config = {
            'hyperparameters': {'window_size': 50},
            'dataset_stats': {'mean': 0.5, 'std': 0.1},
            'inference_results': {'accuracy': 0.95},
            'simulation_metrics': {'snr': 1.2}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Create empty state file
        with open(state_path, 'w') as f:
            yaml.dump({}, f)
        
        # Mock the global paths
        import code.src.utils.migrate_config as mc
        original_config_path = mc.CONFIG_PATH
        original_state_path = mc.STATE_PATH
        original_max_size = mc.MAX_CONFIG_SIZE
        
        mc.CONFIG_PATH = config_path
        mc.STATE_PATH = state_path
        mc.MAX_CONFIG_SIZE = 2048
        
        try:
            result = mc.migrate_config()
            
            # Verify migration result
            assert result is True
            
            # Verify config no longer has the keys
            config_after = load_yaml(config_path)
            for key in KEYS_TO_MIGRATE:
                assert key not in config_after
            
            # Verify state has the keys
            state_after = load_yaml(state_path)
            assert 'projects' in state_after
            proj_key = "PROJ-024-test"
            assert proj_key in state_after['projects']
            assert 'derived_statistics' in state_after['projects'][proj_key]
            
            derived = state_after['projects'][proj_key]['derived_statistics']
            assert 'dataset_stats' in derived
            assert 'inference_results' in derived
            assert 'simulation_metrics' in derived
            
        finally:
            # Restore original paths
            mc.CONFIG_PATH = original_config_path
            mc.STATE_PATH = original_state_path
            mc.MAX_CONFIG_SIZE = original_max_size

    def test_config_size_compliance(self, tmp_path):
        """Test that migration enforces config size limit."""
        config_path = tmp_path / "code" / "config.yaml"
        state_path = tmp_path / "state" / "projects" / "PROJ-024-test2.yaml"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a config that is intentionally small (under 2KB)
        test_config = {
            'hyperparameters': {'window_size': 50},
            'seeds': {'global_seed': 42}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        with open(state_path, 'w') as f:
            yaml.dump({}, f)
        
        import code.src.utils.migrate_config as mc
        original_config_path = mc.CONFIG_PATH
        original_state_path = mc.STATE_PATH
        original_max_size = mc.MAX_CONFIG_SIZE
        
        mc.CONFIG_PATH = config_path
        mc.STATE_PATH = state_path
        mc.MAX_CONFIG_SIZE = 2048
        
        try:
            result = mc.migrate_config()
            assert result is True
        finally:
            mc.CONFIG_PATH = original_config_path
            mc.STATE_PATH = original_state_path
            mc.MAX_CONFIG_SIZE = original_max_size

    def test_missing_keys_in_config(self, tmp_path):
        """Test migration when some keys are missing from config."""
        config_path = tmp_path / "code" / "config.yaml"
        state_path = tmp_path / "state" / "projects" / "PROJ-024-test3.yaml"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create config with only one of the keys
        test_config = {
            'hyperparameters': {'window_size': 50},
            'dataset_stats': {'mean': 0.5}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        with open(state_path, 'w') as f:
            yaml.dump({}, f)
        
        import code.src.utils.migrate_config as mc
        original_config_path = mc.CONFIG_PATH
        original_state_path = mc.STATE_PATH
        original_max_size = mc.MAX_CONFIG_SIZE
        
        mc.CONFIG_PATH = config_path
        mc.STATE_PATH = state_path
        mc.MAX_CONFIG_SIZE = 2048
        
        try:
            result = mc.migrate_config()
            assert result is True
            
            state_after = load_yaml(state_path)
            derived = state_after['projects']['PROJ-024-test3']['derived_statistics']
            assert 'dataset_stats' in derived
            assert 'inference_results' not in derived
            assert 'simulation_metrics' not in derived
        finally:
            mc.CONFIG_PATH = original_config_path
            mc.STATE_PATH = original_state_path
            mc.MAX_CONFIG_SIZE = original_max_size