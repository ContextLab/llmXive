"""
Unit test for verifying that the parameter increase ratio from research.md is
correctly clamped to the FR‑003 hard cap of 0.30.
"""
import os
import pytest
from config import get_config, get_max_param_increase_percent

def test_param_limit_clamping(tmp_path, monkeypatch):
    # Create a temporary research.md with an excessive ratio
    research_content = """
    ## Methodology for Parameter Limit
    MAX_PARAM_INCREASE_RATIO: 0.85
    """
    research_path = tmp_path / "research.md"
    research_path.write_text(research_content)

    # Patch the path that Config uses to locate research.md
    monkeypatch.setenv("PROJECT_ROOT", str(tmp_path))
    # Re‑initialize config to force re‑parsing
    from importlib import reload
    import config as cfg_mod
    reload(cfg_mod)

    ratio = get_max_param_increase_percent()
    assert ratio is not None
    assert ratio <= 0.30
    assert ratio == 0.30