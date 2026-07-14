"""
Unit tests for the config migration utility.
"""
import os
import tempfile
import yaml
from pathlib import Path
import sys
import pytest

# Add the project root to the path so we can import the utility
# Assuming test is run from project root or similar context
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.utils.migrate_config import migrate_config, load_yaml, save_yaml

@pytest.fixture
def temp_dirs():
    """Create temporary directories for config and state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        code_dir = tmp_path / "code"
        state_dir = tmp_path / "state" / "projects"
        code_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        
        config_path = code_dir / "config.yaml"
        state_path = state_dir / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
        
        yield {
            "config": config_path,
            "state": state_path,
            "root": tmp_path
        }

def test_migrate_existing_keys(temp_dirs):
    """Test migration of keys that exist in config."""
    config_data = {
        "hyperparameters": {"window_size": 50},
        "dataset_stats": {"mean": 10.5, "std": 2.0},
        "inference_results": {"converged": True},
        "simulation_metrics": {"snr": 1.2}
    }
    save_yaml(temp_dirs["config"], config_data)
    
    # Mock the global paths in the module
    import code.src.utils.migrate_config as mc
    original_config_path = mc.CONFIG_PATH
    original_state_path = mc.STATE_PATH
    
    mc.CONFIG_PATH = temp_dirs["config"]
    mc.STATE_PATH = temp_dirs["state"]
    
    try:
        result = migrate_config()
        assert result is True
        
        # Verify config no longer has the keys
        updated_config = load_yaml(temp_dirs["config"])
        assert "dataset_stats" not in updated_config
        assert "inference_results" not in updated_config
        assert "simulation_metrics" not in updated_config
        
        # Verify state has the keys
        updated_state = load_yaml(temp_dirs["state"])
        assert "projects" in updated_state
        proj_data = updated_state["projects"]["PROJ-024-bayesian-nonparametrics-for-anomaly-dete"]
        assert "derived_statistics" in proj_data
        assert "dataset_stats" in proj_data["derived_statistics"]
        assert proj_data["derived_statistics"]["dataset_stats"]["mean"] == 10.5
    finally:
        mc.CONFIG_PATH = original_config_path
        mc.STATE_PATH = original_state_path

def test_migrate_missing_keys(temp_dirs):
    """Test migration when keys are missing in config (should initialize empty in state)."""
    config_data = {
        "hyperparameters": {"window_size": 50}
    }
    save_yaml(temp_dirs["config"], config_data)
    
    import code.src.utils.migrate_config as mc
    original_config_path = mc.CONFIG_PATH
    original_state_path = mc.STATE_PATH
    
    mc.CONFIG_PATH = temp_dirs["config"]
    mc.STATE_PATH = temp_dirs["state"]
    
    try:
        result = migrate_config()
        assert result is True
        
        # Verify config is unchanged
        updated_config = load_yaml(temp_dirs["config"])
        assert updated_config == config_data
        
        # Verify state has empty dicts for missing keys
        updated_state = load_yaml(temp_dirs["state"])
        proj_data = updated_state["projects"]["PROJ-024-bayesian-nonparametrics-for-anomaly-dete"]
        assert "dataset_stats" in proj_data["derived_statistics"]
        assert proj_data["derived_statistics"]["dataset_stats"] == {}
    finally:
        mc.CONFIG_PATH = original_config_path
        mc.STATE_PATH = original_state_path

def test_config_size_limit_exceeded(temp_dirs):
    """Test that migration fails if config exceeds size limit after removal."""
    # Create a config that is just under the limit, but with huge keys
    # Actually, if we remove keys, it should be smaller. 
    # To test failure, we need a config that is still too big after removal.
    # But the task is to remove keys. If the remaining config is too big, it's a pre-existing issue.
    # Let's test the logic: if the file is too big, return False.
    
    # Create a config with a huge value that stays
    large_value = "x" * 3000
    config_data = {
        "hyperparameters": {"window_size": 50, "huge": large_value},
        "dataset_stats": {"val": 1}
    }
    save_yaml(temp_dirs["config"], config_data)
    
    import code.src.utils.migrate_config as mc
    original_config_path = mc.CONFIG_PATH
    original_state_path = mc.STATE_PATH
    
    mc.CONFIG_PATH = temp_dirs["config"]
    mc.STATE_PATH = temp_dirs["state"]
    
    try:
        # This should return False because even after removing dataset_stats, 
        # the huge key makes it > 2048 bytes
        result = migrate_config()
        assert result is False
    finally:
        mc.CONFIG_PATH = original_config_path
        mc.STATE_PATH = original_state_path