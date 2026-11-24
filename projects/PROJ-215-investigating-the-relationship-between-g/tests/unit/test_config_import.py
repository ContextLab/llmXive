"""
Unit test for ``code/config.py`` importability and constant definitions.

The test simply imports the module and checks that the expected public
attributes exist and have the correct basic types.  No external data or
environment variables are required.
"""

import importlib

def test_config_import_and_constants():
    # Import the module dynamically to ensure any import‑time side effects are
    # exercised.
    cfg = importlib.import_module("config")

    # Verify that the module defines the expected constants.
    assert hasattr(cfg, "PREVALENCE_THRESHOLD")
    assert isinstance(cfg.PREVALENCE_THRESHOLD, float)
    assert cfg.PREVALENCE_THRESHOLD == 0.001

    assert hasattr(cfg, "RAREFACTION_LOSS_CUTOFF")
    assert isinstance(cfg.RAREFACTION_LOSS_CUTOFF, float)
    assert cfg.RAREFACTION_LOSS_CUTOFF == 0.20

    # Verify that the path constants are strings.
    for name in ("LOGS_DIR", "DATA_DIR", "CODE_DIR", "RESULTS_DIR", "FIGURES_DIR"):
        assert hasattr(cfg, name)
        value = getattr(cfg, name)
        assert isinstance(value, str)
        # The path should exist (directories are created lazily by other scripts,
        # but the helper functions can be called without error).
        # We do not enforce existence here to keep the test lightweight.

    # Environment variables may be None if no .env file is present.
    # They should be present as attributes.
    assert hasattr(cfg, "AGP_STUDY_ID")
    assert hasattr(cfg, "DATA_URL")
    # Both should be either ``str`` or ``None``.
    assert isinstance(cfg.AGP_STUDY_ID, (str, type(None)))
    assert isinstance(cfg.DATA_URL, (str, type(None)))

    # Helper function should be callable.
    assert callable(cfg.verify_required_env_vars)