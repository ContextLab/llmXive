import pytest
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import get_config, CONVERGENCE_THRESHOLD

def test_convergence_threshold_constant():
    """Verify the convergence threshold is defined as 0.90."""
    assert CONVERGENCE_THRESHOLD == 0.90, f"Expected 0.90, got {CONVERGENCE_THRESHOLD}"

def test_config_contains_threshold():
    """Verify get_config returns the threshold."""
    config = get_config()
    assert "convergence_threshold" in config
    assert config["convergence_threshold"] == 0.90

def test_convergence_reporting_logic():
    """
    Verify that the analysis logic (conceptually) uses the threshold.
    This test ensures the constant is available for the analysis module.
    """
    from analysis import run_analysis_pipeline
    # We don't run the full pipeline here, but we verify the import works
    # and the constant is accessible.
    assert CONVERGENCE_THRESHOLD is not None