import pytest
import importlib
import sys
from data.loaders import get_dataset, verify_datasets

def test_verify_datasets_raises_import_error(monkeypatch):
    # Simulate missing real dataset module
    monkeypatch.setitem(sys.modules, "real_dataset", None)
    with pytest.raises(ImportError):
        verify_datasets()

def test_get_dataset_uses_synthetic_when_no_real_dataset(monkeypatch):
    # Ensure real dataset import fails
    monkeypatch.setitem(sys.modules, "real_dataset", None)
    dataset = get_dataset("synthetic")
    assert dataset is not None
