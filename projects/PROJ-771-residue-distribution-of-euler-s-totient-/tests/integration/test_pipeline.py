"""Integration test for the full pipeline (T024)."""
import os
import json
import pytest
from pathlib import Path

def test_pipeline_artifacts_exist():
    """Verify all expected directories and placeholder files exist."""
    base = Path(".")
    expected_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/plots",
        "results/reports",
        "tests/unit",
        "tests/integration"
    ]
    for d in expected_dirs:
        assert (base / d).exists(), f"Directory {d} is missing"

def test_run_analysis_imports():
    """Verify run_analysis can be imported without errors."""
    from run_analysis import main, load_config, pin_orchestration_seed
    assert callable(main)
    assert callable(load_config)
    assert callable(pin_orchestration_seed)
