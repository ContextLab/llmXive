import os
import builtins
import pytest
from unittest import mock

# The script under test raises DataFetchError when the dataset cannot be loaded.
from data_prep import DataFetchError

# Import the main function via the script's module name.
import importlib.util
import pathlib

SCRIPT_PATH = pathlib.Path(__file__).parent.parent / "code" / "01_ingest_and_filter.py"

spec = importlib.util.spec_from_file_location("ingest_and_filter", SCRIPT_PATH)
ingest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest_module)


def test_fetch_failure_raises_datafetcherror(monkeypatch):
    """
    Simulate a failure to load the dataset by setting an invalid
    ``VERIFIED_DATA_SOURCE`` and mocking ``datasets.load_dataset`` to raise.
    The script should propagate a ``DataFetchError``.
    """
    # Force the script to use a verified source that does not exist.
    monkeypatch.setenv("VERIFIED_DATA_SOURCE", "nonexistent/dataset")

    # Patch the load_dataset function to raise an exception.
    with mock.patch("datasets.load_dataset", side_effect=Exception("load failure")):
        with pytest.raises(DataFetchError):
            ingest_module.ingest_and_filter(num_samples=1, tags=["social"])