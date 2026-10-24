import pytest
from unittest import mock
from pathlib import Path
import importlib.util
from data_prep import DataFetchError

# Dynamically load the script to test its internal function
SCRIPT_PATH = Path(__file__).parents[2] / "code" / "01_ingest_and_filter.py"
spec = importlib.util.spec_from_file_location("ingest_and_filter", SCRIPT_PATH)
ingest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_module)

def test_fetch_failure_raises_datafetcherror():
    """
    Simulate a failure to load the dataset using FiftyOne and assert that 
    DataFetchError is raised.
    """
    # Mock foz.load_zoo_dataset to raise an exception
    with mock.patch("fiftyone.zoo.load_zoo_dataset", side_effect=Exception("Zoo Load Error")):
        with pytest.raises(DataFetchError) as excinfo:
            ingest_module.ingest_and_filter(num_samples=1, tags=["social"])
        assert "Unable to load Open Images dataset via FiftyOne" in str(excinfo.value)

def test_missing_fiftyone_raises_datafetcherror(monkeypatch):
    """
    Simulate FiftyOne not being imported/installed.
    """
    # We can't easily 'un-import' fiftyone, but we can mock the module 
    # in the ingest_module's namespace.
    ingest_module.foz = None
    with pytest.raises(DataFetchError) as excinfo:
        ingest_module.ingest_and_filter(num_samples=1, tags=["social"])
    assert "FiftyOne is not installed" in str(excinfo.value)