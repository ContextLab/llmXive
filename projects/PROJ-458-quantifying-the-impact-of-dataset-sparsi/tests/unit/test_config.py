import importlib
import sys

import pytest

def test_load_env_missing_key(monkeypatch):
    """
    Verify that load_env() raises RuntimeError when MP_API_KEY is absent.
    """
    # Ensure the variable is not set in the environment
    monkeypatch.delenv("MP_API_KEY", raising=False)

    # Reload the config module to pick up the changed environment
    if "config" in sys.modules:
        del sys.modules["config"]
    import config

    with pytest.raises(RuntimeError):
        config.load_env()

def test_constants_defined():
    """
    Basic sanity check that the required constants exist and have the correct types.
    """
    import config

    assert isinstance(config.SEED_LIST, list) and all(isinstance(s, int) for s in config.SEED_LIST)
    assert isinstance(config.SPARSITY_LEVELS, list) and all(isinstance(p, int) for p in config.SPARSITY_LEVELS)