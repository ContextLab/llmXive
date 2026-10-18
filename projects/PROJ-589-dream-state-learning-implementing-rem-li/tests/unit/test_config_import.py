"""
Unit test to ensure that the configuration module can be imported
after a fresh ``pip install -r code/requirements.txt``.
The test simply imports ``config`` and constructs a ``Config`` instance.
"""

import importlib

def test_config_importable():
    cfg_module = importlib.import_module("config")
    cfg = cfg_module.Config()
    assert cfg.device.type == "cpu"
    assert cfg.warm_up_steps == 20
    assert cfg.dream_ratio == 5
    # Verify that the memory‑limit check does not raise on the test runner
    assert cfg.memory_limit_bytes == int(6.3 * 1024 ** 3)