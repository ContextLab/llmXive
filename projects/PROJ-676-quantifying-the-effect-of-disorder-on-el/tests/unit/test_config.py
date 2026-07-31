import pytest
from code.config import get_config

def test_config_keys_exist():
    """Verify all required keys exist in the config dictionary."""
    config = get_config()
    
    required_keys = [
        "W_LIST", "L_LIST", "NUM_REALIZATIONS", "SEED",
        "WEAK_DISORDER_CUTOFF", "NUMERICAL_RESIDUAL_THRESHOLD", "MAX_TM_ITERATIONS"
    ]
    
    for key in required_keys:
        assert key in config, f"Missing required key: {key}"

def test_config_values_non_empty():
    """Verify lists are non-empty and numbers are valid."""
    config = get_config()
    
    assert len(config["W_LIST"]) > 0, "W_LIST must be non-empty"
    assert len(config["L_LIST"]) > 0, "L_LIST must be non-empty"
    assert isinstance(config["NUM_REALIZATIONS"], int) and config["NUM_REALIZATIONS"] > 0
    assert isinstance(config["SEED"], int)
    assert isinstance(config["WEAK_DISORDER_CUTOFF"], (int, float))
    assert isinstance(config["NUMERICAL_RESIDUAL_THRESHOLD"], (int, float))
    assert isinstance(config["MAX_TM_ITERATIONS"], int)

def test_config_types():
    """Verify types of config values."""
    config = get_config()
    
    assert all(isinstance(w, (int, float)) for w in config["W_LIST"]), "W_LIST must contain numbers"
    assert all(isinstance(l, int) for l in config["L_LIST"]), "L_LIST must contain integers"
