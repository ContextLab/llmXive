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
    Simulate a failure to load the dataset using HF datasets and assert that 
    DataFetchError is raised.
    """
    # Mock load_dataset to raise an exception
    with mock.patch("ingest_and_filter.load_dataset", side_effect=Exception("HF Load Error")):
        with pytest.raises(DataFetchError) as excinfo:
            ingest_module.ingest_and_filter(num_samples=1, tags=["social"])
        assert "Unable to load Open Images dataset" in str(excinfo.value)

def test_no_matches_raises_datafetcherror():
    """
    Simulate a case where the dataset loads but no images match the tags.
    """
    # Mock load_dataset to return an empty generator
    with mock.patch("ingest_and_filter.load_dataset", return_value=iter([])):
        with pytest.raises(DataFetchError) as excinfo:
            ingest_module.ingest_and_filter(num_samples=1, tags=["nonexistent_tag"])
        assert "No candidate images matched the filtering criteria" in str(excinfo.value)