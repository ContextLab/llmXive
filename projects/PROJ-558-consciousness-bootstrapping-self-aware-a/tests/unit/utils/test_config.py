import pytest
from utils.logging import ConfigurationError
from code.utils.config import Config, validate_config, get_config, set_config

def test_token_limit_must_be_100000():
    """
    Test that token_limit must be exactly 100000.
    Any other value (including defaults if changed, or 'deferred') must raise ConfigurationError.
    """
    # Test valid case
    valid_config = Config(token_limit=100000)
    try:
        validate_config(valid_config)
    except ConfigurationError:
        pytest.fail("Valid token_limit=100000 raised ConfigurationError unexpectedly.")

    # Test invalid cases
    invalid_values = [99999, 100001, 0, 50000, None]
    
    for val in invalid_values:
        # Handle None explicitly as it would cause a type error in comparison if not checked
        if val is None:
            invalid_config = Config(token_limit=100000) # Create valid first to avoid init error
            invalid_config.token_limit = None # Force set to None
        else:
            invalid_config = Config(token_limit=val)
        
        with pytest.raises(ConfigurationError, match="token_limit must be exactly 100000"):
            validate_config(invalid_config)

def test_recursion_depth_limit():
    """
    Test that recursion_depth cannot exceed 2.
    """
    valid_config = Config(recursion_depth=2)
    try:
        validate_config(valid_config)
    except ConfigurationError:
        pytest.fail("Valid recursion_depth=2 raised ConfigurationError unexpectedly.")
    
    invalid_config = Config(recursion_depth=3)
    with pytest.raises(ConfigurationError, match="recursion_depth cannot exceed 2"):
        validate_config(invalid_config)

def test_get_config_initialization():
    """
    Test that get_config initializes with correct defaults and validates.
    """
    # Reset global state for clean test
    from code.utils import config
    config._config = None
    
    cfg = get_config()
    assert cfg.token_limit == 100000
    assert cfg.recursion_depth == 2
    assert cfg.seed == 42

def test_set_config_updates_global():
    """
    Test that set_config updates the global instance.
    """
    from code.utils import config
    config._config = None # Reset
    
    new_cfg = Config(token_limit=100000, batch_size=8, learning_rate=5e-5)
    set_config(new_cfg)
    
    retrieved = get_config()
    assert retrieved.batch_size == 8
    assert retrieved.learning_rate == 5e-5
    assert retrieved.token_limit == 100000