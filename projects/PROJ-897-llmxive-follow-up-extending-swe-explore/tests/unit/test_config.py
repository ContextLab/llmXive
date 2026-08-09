"""
Unit tests for the configuration module (T002).
Verifies that constants are defined, paths resolve correctly,
and deferred parameters handle None/Env vars gracefully.
"""
import os
import sys
from pathlib import Path
import pytest

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    HARD_INSTANCE_PERCENTILE,
    COVERAGE_COLUMN_NAME,
    SWEEP_SAMPLE_SIZE,
    SWEEP_SEED,
    TURN_LIMITS,
    MIN_SYNTHETIC_ISSUES,
    VALIDATION_SAMPLE_SIZE,
    TIE_THRESHOLD,
    MAX_RUNTIME_HOURS,
    MODEL_PRECISION,
    get_path,
    ensure_directories,
    resolve_deferred_config,
    get_config_summary,
    DATA_RAW,
    DATA_CURATED,
)


def test_constant_values():
    """Verify that concrete constants have the expected values."""
    assert COVERAGE_COLUMN_NAME == 'initial_coverage'
    assert SWEEP_SEED == 42
    assert TURN_LIMITS == [1, 2, 3]
    assert TIE_THRESHOLD == 0.50
    assert MAX_RUNTIME_HOURS == 6
    assert MODEL_PRECISION == '8-bit'

def test_deferred_constants_are_none():
    """Verify that deferred constants are initially None."""
    assert HARD_INSTANCE_PERCENTILE is None
    assert SWEEP_SAMPLE_SIZE is None
    assert MIN_SYNTHETIC_ISSUES is None
    assert VALIDATION_SAMPLE_SIZE is None

def test_get_path():
    """Verify path construction logic."""
    base = Path("/root")
    result = get_path(base, "sub", "file.txt")
    assert result == Path("/root/sub/file.txt")

def test_ensure_directories_creates_folders(tmp_path):
    """Verify that ensure_directories creates the required folders."""
    # Temporarily override DATA_ROOT for this test
    import config
    original_data_root = config.DATA_ROOT
    config.DATA_ROOT = tmp_path
    config.DATA_RAW = tmp_path / "raw"
    config.DATA_CURATED = tmp_path / "curated"
    config.DATA_RESULTS = tmp_path / "results"
    config.STATE_ROOT = tmp_path / "state"
    config.PAPER_ROOT = tmp_path / "paper"
    config.DATA_FIGURES = tmp_path / "figures"

    try:
        ensure_directories()
        assert (tmp_path / "raw").exists()
        assert (tmp_path / "curated").exists()
        assert (tmp_path / "results").exists()
        assert (tmp_path / "state").exists()
        assert (tmp_path / "paper").exists()
        assert (tmp_path / "figures").exists()
    finally:
        # Restore original
        config.DATA_ROOT = original_data_root

def test_resolve_deferred_config_with_env_vars(monkeypatch):
    """Test that environment variables correctly override None defaults."""
    monkeypatch.setenv("HARD_INSTANCE_PERCENTILE", "0.15")
    monkeypatch.setenv("SWEEP_SAMPLE_SIZE", "100")
    
    resolved = resolve_deferred_config()
    
    assert resolved["HARD_INSTANCE_PERCENTILE"] == 0.15
    assert resolved["SWEEP_SAMPLE_SIZE"] == 100
    # Others should remain None if not set
    assert resolved.get("MIN_SYNTHETIC_ISSUES") is None

def test_get_config_summary():
    """Verify that get_config_summary returns a valid dictionary."""
    summary = get_config_summary()
    assert isinstance(summary, dict)
    assert "hard_instance_percentile" in summary
    assert "sweep_seed" in summary
    assert summary["sweep_seed"] == 42
