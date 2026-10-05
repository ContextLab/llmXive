"""
Unit tests for the configuration module.
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
import config

def test_project_root_exists():
    """Verify PROJECT_ROOT is a valid Path object."""
    assert isinstance(config.PROJECT_ROOT, Path)
    assert config.PROJECT_ROOT.exists()

def test_directory_paths_exist():
    """Verify that expected directory paths are constructed correctly."""
    # Note: We don't assert they exist on disk if they haven't been created yet (T001),
    # but we verify the Path construction logic.
    assert isinstance(config.DATA_RAW_DIR, Path)
    assert isinstance(config.DATA_PROCESSED_DIR, Path)
    assert isinstance(config.DATA_MODELS_DIR, Path)
    assert isinstance(config.CODE_DIR, Path)
    assert isinstance(config.TESTS_DIR, Path)
    assert isinstance(config.RESULTS_DIR, Path)
    assert isinstance(config.STATE_DIR, Path)

def test_random_seed():
    """Verify random seed is an integer."""
    assert isinstance(config.RANDOM_SEED, int)
    assert config.RANDOM_SEED == 42

def test_thresholds():
    """Verify threshold values are set correctly."""
    assert isinstance(config.VIF_THRESHOLD, float)
    assert config.VIF_THRESHOLD == 5.0
    assert isinstance(config.IMPUTATION_THRESHOLD_DAYS, int)
    assert config.IMPUTATION_THRESHOLD_DAYS == 30
    assert isinstance(config.MAX_RAM_GB, int)
    assert config.MAX_RAM_GB == 6
    assert config.DATA_GAP_HALT is True

def test_urls_are_strings():
    """Verify all URL configurations are non-empty strings."""
    urls = [
        config.NOAA_URL,
        config.UNEP_URL,
        config.CORAL_TRAIT_URL,
        config.REEFBASE_URL,
        config.RASTER_2024_URL,
        config.INDEPENDENT_BLEACHING_URL
    ]
    for url in urls:
        assert isinstance(url, str)
        assert len(url) > 0
        assert url.startswith("http")

def test_validate_urls_raises_on_failure(monkeypatch):
    """Test that validate_urls raises an error when a URL fails."""
    # Mock requests.head to simulate a failure
    import requests
    original_head = requests.head
    
    def mock_head(url, *args, **kwargs):
        raise requests.exceptions.ConnectionError("Mocked connection error")
    
    monkeypatch.setattr(requests, 'head', mock_head)
    
    # Also need to mock get if head fails with 405 logic, but for simplicity
    # we assume the first call fails.
    
    with pytest.raises(ConnectionError):
        config.validate_urls(timeout=1.0)
    
    # Restore
    monkeypatch.setattr(requests, 'head', original_head)