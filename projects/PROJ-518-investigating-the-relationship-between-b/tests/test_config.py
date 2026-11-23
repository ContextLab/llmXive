import importlib
import os

import pytest

# Import the module under test
import config as cfg_module

def test_default_fwe_method_is_valid():
    """The default configuration should pass validation."""
    cfg = cfg_module.get_config()
    assert cfg.FWE_METHOD == "max-t"
    # Should not raise
    cfg_module.validate_fwe_config()

def test_invalid_fwe_method_raises(monkeypatch):
    """Setting an unsupported FWE_METHOD should raise a ValueError."""
    # Override environment variable before the Config singleton is created
    monkeypatch.setenv("FWE_METHOD", "invalid_method")

    # Reload the config module to reset the cached singleton
    importlib.reload(cfg_module)

    cfg = cfg_module.get_config()
    assert cfg.FWE_METHOD == "invalid_method"

    with pytest.raises(ValueError) as excinfo:
        cfg_module.validate_fwe_config()
    assert "Invalid FWE_METHOD" in str(excinfo.value)