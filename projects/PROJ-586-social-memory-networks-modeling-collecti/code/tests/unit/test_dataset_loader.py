"""Test that the dataset loader fails gracefully when the optional
``datasets`` package is not available."""
import importlib
import sys

from data.loaders import get_dataset, verify_datasets

def test_verify_datasets_raises_import_error(monkeypatch):
    # Simulate ``datasets`` not being installed.
    monkeypatch.setitem(sys.modules, "datasets", None)
    # Reload the module to pick up the mocked import state.
    importlib.reload(importlib.import_module("data.loaders"))
    with pytest.raises(ModuleNotFoundError):
        verify_datasets()

def test_get_dataset_uses_synthetic_when_no_real_dataset(monkeypatch):
    # Force ``datasets`` import to fail, then request a synthetic dataset.
    monkeypatch.setitem(sys.modules, "datasets", None)
    importlib.reload(importlib.import_module("data.loaders"))
    ds = get_dataset("synthetic")
    assert ds is not None  # synthetic fallback should be returned