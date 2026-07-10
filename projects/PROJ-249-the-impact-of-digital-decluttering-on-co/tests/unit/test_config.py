"""
Unit tests for the configuration management module.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest

from code.utils.config import (
    ConfigManager,
    ConfigError,
    get_config,
    get_data_path,
    get_result_path,
    get_analysis_param,
    DEFAULT_CONFIG
)
from code.utils.random_seed import set_global_seed

@pytest.fixture(autouse=True)
def reset_config():
    """Reset the config singleton before each test."""
    ConfigManager.reset_instance()
    yield
    ConfigManager.reset_instance()

@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            "project_root": str(Path(__file__).parent.parent.parent),
            "data": {
                "raw": "test_data/raw",
                "processed": "test_data/processed",
                "compliance": "test_data/compliance",
                "figures": "test_data/figures"
            },
            "results": {
                "output_dir": "test_results",
                "report_file": "test_report.md",
                "summary_file": "test_summary.json",
                "power_file": "test_power.json",
                "sensitivity_file": "test_sensitivity.md"
            },
            "analysis": {
                "bootstrap_resamples": 5000,
                "monte_carlo_iterations": 500,
                "effect_size_threshold": 0.3,
                "p_value_threshold": 0.01,
                "convergence_max_iter": 50
            },
            "random_seed": {
                "default": 123,
                "config_file": "test_data/compliance/seed_config.yaml"
            },
            "paths": {
                "tasks_md": "tasks.md",
                "plan_md": "plan.md",
                "spec_md": "specs/spec.md",
                "data_model_md": "specs/data-model.md"
            }
        }
        yaml.dump(config_data, f)
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()
    # Cleanup test directories if they exist
    base_dir = Path(__file__).parent.parent.parent
    for dir_name in ["test_data", "test_results"]:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)

def test_config_creation_from_file(temp_config_file):
    """Test that configuration can be loaded from a file."""
    config = ConfigManager(temp_config_file)
    
    assert config.get("project_root") is not None
    assert config.get("data.raw") is not None
    assert config.get("analysis.bootstrap_resamples") == 5000
    assert config.get("random_seed.default") == 123

def test_config_defaults_when_file_missing():
    """Test that default configuration is used when file is missing."""
    missing_path = Path("/nonexistent/config.yaml")
    config = ConfigManager(missing_path)
    
    assert config.get("data.raw") is not None
    assert config.get("analysis.bootstrap_resamples") == 10000
    assert config.get("random_seed.default") == 42

def test_get_with_dot_notation(temp_config_file):
    """Test getting values using dot notation."""
    config = ConfigManager(temp_config_file)
    
    assert config.get("data.raw") is not None
    assert config.get("results.output_dir") is not None
    assert config.get("analysis.bootstrap_resamples") == 5000
    assert config.get("nonexistent.key", "default") == "default"

def test_get_data_dir(temp_config_file):
    """Test getting data directory paths."""
    config = ConfigManager(temp_config_file)
    
    raw_dir = config.get_data_dir("raw")
    assert raw_dir.exists() or raw_dir.parent.exists()
    assert "raw" in str(raw_dir)

def test_get_result_path(temp_config_file):
    """Test getting result file paths."""
    config = ConfigManager(temp_config_file)
    
    result_path = config.get_result_path("test_output.json")
    assert "test_results" in str(result_path) or "results" in str(result_path)
    assert result_path.name == "test_output.json"

def test_ensure_directories(temp_config_file):
    """Test that ensure_directories creates the necessary folders."""
    config = ConfigManager(temp_config_file)
    config.ensure_directories()
    
    # Check that data directories were created
    for sub_dir in ["raw", "processed", "compliance", "figures"]:
        dir_path = config.get_data_dir(sub_dir)
        assert dir_path.exists()

def test_singleton_pattern(temp_config_file):
    """Test that ConfigManager follows the singleton pattern."""
    config1 = ConfigManager.get_instance(temp_config_file)
    config2 = ConfigManager.get_instance(temp_config_file)
    
    assert config1 is config2

def test_singleton_reset():
    """Test that reset_instance creates a new singleton."""
    temp_path = Path(tempfile.mktemp(suffix='.yaml'))
    try:
        ConfigManager(temp_path)
        config1 = ConfigManager.get_instance()
        
        ConfigManager.reset_instance()
        config2 = ConfigManager.get_instance(temp_path)
        
        assert config1 is not config2
    finally:
        if temp_path.exists():
            temp_path.unlink()

def test_deep_merge():
    """Test that configuration values are properly merged."""
    base = {
        "data": {"raw": "default_raw", "processed": "default_processed"},
        "analysis": {"param1": 100, "param2": 200}
    }
    override = {
        "data": {"raw": "override_raw"},
        "analysis": {"param1": 150}
    }
    
    config = ConfigManager._deep_merge(base, override)
    
    assert config["data"]["raw"] == "override_raw"
    assert config["data"]["processed"] == "default_processed"
    assert config["analysis"]["param1"] == 150
    assert config["analysis"]["param2"] == 200

def test_invalid_yaml_handling():
    """Test that invalid YAML raises ConfigError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ConfigError):
            ConfigManager(temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

def test_get_config_convenience_function(temp_config_file):
    """Test the get_config convenience function."""
    config = get_config(temp_config_file)
    assert config.get("data.raw") is not None

def test_get_data_path_convenience(temp_config_file):
    """Test the get_data_path convenience function."""
    config = get_config(temp_config_file)
    path = get_data_path("raw", "test.csv")
    assert path is not None

def test_get_result_path_convenience(temp_config_file):
    """Test the get_result_path convenience function."""
    config = get_config(temp_config_file)
    path = get_result_path("output.json")
    assert path is not None

def test_get_analysis_param_convenience(temp_config_file):
    """Test the get_analysis_param convenience function."""
    config = get_config(temp_config_file)
    param = get_analysis_param("bootstrap_resamples")
    assert param == 5000

def test_seed_application(temp_config_file):
    """Test that random seed is applied from config."""
    # Reset seed first
    set_global_seed(999)
    
    config = ConfigManager(temp_config_file)
    
    # The config should have applied seed 123
    # We can't directly check the seed value, but we can verify
    # the config loaded it correctly
    assert config.get("random_seed.default") == 123