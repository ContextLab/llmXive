import pytest
from unittest import mock
from pathlib import Path
import importlib.util

# Import DataFetchError from data_prep
from data_prep import DataFetchError

# Dynamically load the script to test its internal function
# Resolve the correct path to the script located at the project root /code/
SCRIPT_PATH = Path(__file__).parents[2] / "code" / "01_ingest_and_filter.py"
spec = importlib.util.spec_from_file_location("ingest_and_filter", SCRIPT_PATH)
ingest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_module)

def test_fetch_failure_raises_datafetcherror(monkeypatch):
    """
    Simulate a failure to load the dataset and assert that 
    DataFetchError is raised.
    """
    # Force an invalid source via environment variable
    monkeypatch.setenv("VERIFIED_DATA_SOURCE", "invalid/source")

    # Mock load_dataset to raise an exception
    with mock.patch("datasets.load_dataset", side_effect=Exception("HF Load Error")):
        with pytest.raises(DataFetchError) as excinfo:
            ingest_module.ingest_and_filter(num_samples=1, tags=["social"])
        assert "Unable to load Open Images dataset" in str(excinfo.value)