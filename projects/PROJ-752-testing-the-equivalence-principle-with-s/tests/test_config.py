"""
Tests for the config module.
"""
import os
import pytest
from code.config import Config, config, get_config


def test_config_defaults():
    """Test that default values are set correctly."""
    cfg = Config()
    assert cfg.residual_threshold_m == 0.02
    assert cfg.convergence_tolerance == 1e-5
    assert "LAGEOS-1" in cfg.verified_dataset_urls
    assert "Starlette" in cfg.verified_dataset_urls

def test_config_paths_exist(tmp_path):
    """Test that config creates required directories."""
    # Create a temp config with a specific root
    cfg = Config(root_dir=str(tmp_path))
    
    # Check that the data directory was created
    data_path = os.path.join(str(tmp_path), cfg.data_dir)
    assert os.path.exists(data_path)

def test_get_config_singleton():
    """Test that get_config returns the same instance."""
    cfg1 = get_config()
    cfg2 = get_config()
    assert cfg1 is cfg2

def test_verified_urls_format():
    """Test that verified dataset URLs are valid strings."""
    urls = config.verified_dataset_urls
    for sat_id, url in urls.items():
        assert isinstance(url, str)
        assert url.startswith("http")
        assert sat_id in ["LAGEOS-1", "LAGEOS-2", "Etalon-1", "Etalon-2", "Starlette"]
