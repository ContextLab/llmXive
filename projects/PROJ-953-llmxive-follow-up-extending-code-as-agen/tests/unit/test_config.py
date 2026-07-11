"""
Unit tests for the configuration loader.
"""
import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import Config, get_config, reset_config, _PROJECT_ROOT

def test_config_defaults():
    """Test that config loads with default values when no env vars are set."""
    # Clear specific env vars to test defaults
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("LLMXIVE")}
    
    cfg = Config(clean_env)
    
    assert isinstance(cfg.data_dir, Path)
    assert isinstance(cfg.data_raw, Path)
    assert isinstance(cfg.data_processed, Path)
    assert isinstance(cfg.execution_timeout_seconds, int)
    assert cfg.execution_timeout_seconds == 300
    assert cfg.max_workers == 4
    assert cfg.swebench_dataset_name == "princeton-nlp/SWE-bench_Lite"

def test_config_env_override():
    """Test that environment variables override defaults."""
    test_env = {
        "LLMXIVE_DATA_DIR": "/tmp/test_data",
        "LLMXIVE_DATA_RAW": "/tmp/test_data/raw",
        "LLMXIVE_DATA_PROCESSED": "/tmp/test_data/processed",
        "LLMXIVE_DATA_GRAPHS": "/tmp/test_data/graphs",
        "LLMXIVE_MODELS_DIR": "/tmp/test_models",
        "LLMXIVE_CONTRACTS_DIR": "/tmp/test_contracts",
        "LLMXIVE_DATA_PROCESSED": "/tmp/test_data/processed", # Ensure processed is set
        "SWEBENCH_DATASET_NAME": "custom/swe-bench",
        "EXECUTION_TIMEOUT_SECONDS": "600",
        "MAX_WORKERS": "8"
    }
    
    cfg = Config(test_env)
    
    assert str(cfg.data_dir) == "/tmp/test_data"
    assert str(cfg.data_raw) == "/tmp/test_data/raw"
    assert str(cfg.data_processed) == "/tmp/test_data/processed"
    assert str(cfg.data_graphs) == "/tmp/test_data/graphs"
    assert str(cfg.models_dir) == "/tmp/test_models"
    assert str(cfg.contracts_dir) == "/tmp/test_contracts"
    assert cfg.swebench_dataset_name == "custom/swe-bench"
    assert cfg.execution_timeout_seconds == 600
    assert cfg.max_workers == 8

def test_config_paths_exist_in_project():
    """Test that resolved paths are within the expected project structure."""
    cfg = Config()
    
    # All data paths should be under the data directory
    assert str(cfg.data_raw).startswith(str(cfg.data_dir))
    assert str(cfg.data_processed).startswith(str(cfg.data_dir))
    assert str(cfg.data_graphs).startswith(str(cfg.data_dir))

def test_get_ground_truth_path():
    """Test the helper method for ground truth path."""
    cfg = Config()
    path = cfg.get_ground_truth_path()
    assert path.name == "ground_truth.csv"
    assert path.parent == cfg.data_processed

def test_get_features_path():
    """Test the helper method for features path."""
    cfg = Config()
    path = cfg.get_features_path()
    assert path.name == "features.csv"
    assert path.parent == cfg.data_processed

def test_get_graph_path():
    """Test the helper method for graph path."""
    cfg = Config()
    path = cfg.get_graph_path("task-123")
    assert path.name == "task-123.json"
    assert path.parent == cfg.data_graphs

def test_singleton_pattern():
    """Test that get_config returns the same instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2

def test_reset_config():
    """Test that reset_config creates a new instance with new env."""
    # Reset with a specific env
    test_env = {"LLMXIVE_DATA_DIR": "/tmp/reset_test"}
    new_cfg = reset_config(test_env)
    
    # The global instance should now be the new one
    assert get_config() is new_cfg
    assert str(new_cfg.data_dir) == "/tmp/reset_test"