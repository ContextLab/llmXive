"""Tests for dataset loaders and synthetic fallback functionality."""
import pytest
from pathlib import Path
import tempfile
import os

from data.loaders import (
    register_dataset,
    get_dataset,
    enable_synthetic_fallback,
    disable_synthetic_fallback,
    get_dataset_spec,
    verify_datasets,
    load_experiment_results,
    save_experiment_results,
    _DATASET_REGISTRY,
    _USE_SYNTHETIC_FALLBACK
)


@pytest.fixture(autouse=True)
def reset_registry_and_fallback():
    """Reset registry and fallback state before each test."""
    _DATASET_REGISTRY.clear()
    disable_synthetic_fallback()
    yield
    _DATASET_REGISTRY.clear()
    disable_synthetic_fallback()


def test_register_dataset():
    """Test that datasets can be registered and retrieved."""
    def dummy_loader():
        return {"data": "test"}

    register_dataset("test_ds", dummy_loader)
    
    assert "test_ds" in _DATASET_REGISTRY
    result = get_dataset("test_ds")
    assert result == {"data": "test"}


def test_register_duplicate_raises():
    """Test that registering a duplicate dataset raises ValueError."""
    register_dataset("unique_ds", lambda: {})
    with pytest.raises(ValueError, match="already registered"):
        register_dataset("unique_ds", lambda: {})


def test_get_dataset_not_registered_no_fallback():
    """Test that unregistered dataset raises ImportError when fallback is disabled."""
    disable_synthetic_fallback()
    with pytest.raises(ImportError, match="not registered"):
        get_dataset("nonexistent")


def test_get_dataset_synthetic_fallback():
    """Test that synthetic fallback generates data when enabled."""
    enable_synthetic_fallback()
    disable_synthetic_fallback()  # Ensure clean state
    enable_synthetic_fallback()
    
    # This should not raise and should return synthetic data
    data = get_dataset("fallback_test")
    
    assert isinstance(data, list)
    assert len(data) == 10
    for record in data:
        assert record["is_synthetic"] is True
        assert "game_id" in record
        assert "agent_count" in record


def test_enable_disable_synthetic_fallback():
    """Test toggling synthetic fallback."""
    assert _USE_SYNTHETIC_FALLBACK is False
    
    enable_synthetic_fallback()
    assert _USE_SYNTHETIC_FALLBACK is True
    
    disable_synthetic_fallback()
    assert _USE_SYNTHETIC_FALLBACK is False


def test_get_dataset_spec_registered():
    """Test getting spec for registered dataset."""
    register_dataset("spec_test", lambda: {})
    spec = get_dataset_spec("spec_test")
    
    assert spec["name"] == "spec_test"
    assert "description" in spec


def test_get_dataset_spec_fallback():
    """Test getting spec for unregistered dataset with fallback enabled."""
    enable_synthetic_fallback()
    spec = get_dataset_spec("missing_ds")
    
    assert spec["name"] == "missing_ds"
    assert spec.get("is_synthetic") is True


def test_verify_datasets_all_present():
    """Test verification when all datasets are present."""
    register_dataset("ds1", lambda: {})
    register_dataset("ds2", lambda: {})
    
    # Should not raise
    verify_datasets(["ds1", "ds2"])
    verify_datasets()  # Check all registered


def test_verify_datasets_missing_no_fallback():
    """Test verification fails when datasets are missing and fallback disabled."""
    disable_synthetic_fallback()
    register_dataset("ds1", lambda: {})
    
    with pytest.raises(ImportError, match="Missing required datasets"):
        verify_datasets(["ds1", "missing_ds"])


def test_verify_datasets_missing_with_fallback():
    """Test verification passes with warning when fallback is enabled."""
    enable_synthetic_fallback()
    register_dataset("ds1", lambda: {})
    
    # Should not raise, but might log a warning
    verify_datasets(["ds1", "missing_ds"])


def test_load_experiment_results(tmp_path):
    """Test loading experiment results from CSV."""
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        "game_id,agent_count,context_condition\n"
        "game_1,5,full\n"
        "game_2,3,limited\n"
    )
    
    results = load_experiment_results(csv_path)
    
    assert len(results) == 2
    assert results[0]["game_id"] == "game_1"
    assert results[1]["agent_count"] == "3"


def test_load_experiment_results_not_found():
    """Test loading non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_experiment_results(Path("/nonexistent/path.csv"))


def test_save_experiment_results(tmp_path):
    """Test saving experiment results to CSV."""
    csv_path = tmp_path / "output.csv"
    records = [
        {"game_id": "g1", "agent_count": "5", "context": "full"},
        {"game_id": "g2", "agent_count": "3", "context": "limited"}
    ]
    
    save_experiment_results(csv_path, records)
    
    assert csv_path.exists()
    loaded = load_experiment_results(csv_path)
    assert len(loaded) == 2
    assert loaded[0]["game_id"] == "g1"


def test_save_experiment_results_empty_raises():
    """Test saving empty records raises ValueError."""
    with pytest.raises(ValueError, match="No records to write"):
        save_experiment_results(Path("/tmp/test.csv"), [])


def test_save_and_load_mismatched_keys_raises(tmp_path):
    """Test saving records with mismatched keys raises ValueError."""
    csv_path = tmp_path / "bad.csv"
    records = [
        {"a": "1", "b": "2"},
        {"a": "3", "c": "4"}  # Different keys
    ]
    
    with pytest.raises(ValueError, match="identical keys"):
        save_experiment_results(csv_path, records)