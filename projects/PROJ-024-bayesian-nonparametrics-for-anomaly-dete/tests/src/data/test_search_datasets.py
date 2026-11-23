"""
Unit tests for the ``search_datasets`` script.

The tests verify that the script creates either:
  * at least one file under ``data/raw/`` when a download succeeds, or
  * a ``validation_deferred.md`` report when no download succeeds.

Because the execution environment may not have internet access,
the test mocks ``requests.get`` to simulate both success and failure
scenarios.
"""

import builtins
import io
from pathlib import Path
from unittest import mock

import pytest

from llmxive_toolkit import paths

# Import the module under test
import importlib

search_module = importlib.import_module(
    "code.src.data.search_datasets"
)

@pytest.fixture(autouse=True)
def clean_data_dirs(tmp_path, monkeypatch):
    """
    Ensure that each test runs with a clean ``data`` directory.
    """
    # Redirect the project‑root paths to a temporary location.
    # ``paths`` constructs paths relative to the repository root, so we
    # monkey‑patch its ``root`` attribute.
    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    # Ensure the required parent directories exist.
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "processed" / "results").mkdir(
        parents=True, exist_ok=True
    )
    yield
    # No explicit teardown required – the temporary directory is removed.

def _mock_successful_get(url, *args, **kwargs):
    """
    Return a mock response that behaves like a successful streaming GET.
    """
    mock_resp = mock.Mock()
    mock_resp.iter_content = lambda chunk_size: [b"test data"]
    mock_resp.raise_for_status = lambda: None
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = lambda s, exc_type, exc, tb: None
    return mock_resp

def _mock_failure_get(url, *args, **kwargs):
    """
    Simulate a network error (e.g., 404 or connection error).
    """
    raise requests.exceptions.RequestException("mock failure")

def test_successful_download(monkeypatch):
    """
    When at least one download succeeds, the script should create a file
    under ``data/raw/`` and **not** write the deferred report.
    """
    monkeypatch.setattr(
        "requests.get",
        _mock_successful_get,
    )
    # Run the script
    search_module.main()

    raw_dir = paths.data("raw")
    raw_files = list(raw_dir.glob("*"))
    assert len(raw_files) >= 1, "Expected at least one downloaded file"

    # The deferred report must not exist
    report_path = paths.data(
        "processed", "results", "validation_deferred.md"
    )
    assert not report_path.exists()

def test_all_downloads_fail(monkeypatch):
    """
    When every download fails, the script must generate the
    ``validation_deferred.md`` report and leave ``data/raw/`` empty.
    """
    monkeypatch.setattr(
        "requests.get",
        _mock_failure_get,
    )
    # Run the script
    search_module.main()

    # No files should be present in ``data/raw/``
    raw_dir = paths.data("raw")
    assert not any(raw_dir.iterdir()), "Raw directory should be empty on failure"

    # The deferred report must exist and contain the expected text
    report_path = paths.data(
        "processed", "results", "validation_deferred.md"
    )
    assert report_path.exists()
    content = report_path.read_text()
    assert "Validation Deferred Report" in content
    assert "Result count: 0" in content