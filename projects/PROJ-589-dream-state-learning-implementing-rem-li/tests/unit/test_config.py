"""
Unit test for the project configuration.

Verifies that the configuration module defines the required
MAX_MEMORY_MB constant with the exact value required by the
specification (6 300 MB).
"""

import importlib

def test_max_memory_constant():
    # Import the config module from the code package
    config = importlib.import_module("code.config")
    assert hasattr(config, "MAX_MEMORY_MB"), "MAX_MEMORY_MB constant is missing"
    assert config.MAX_MEMORY_MB == 6300, (
        f"MAX_MEMORY_MB should be 6300, got {config.MAX_MEMORY_MB}"
    )
