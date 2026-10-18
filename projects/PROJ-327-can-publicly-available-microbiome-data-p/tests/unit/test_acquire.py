"""
Unit tests for the ``code.acquire`` module.

The tests focus on the error handling paths required by FR‑008:

* ``test_metabolomics_missing_file`` – simulates a HTTP 404 response
  and expects a ``RuntimeError`` with the exact FR‑008 message.
* ``test_metabolomics_missing_checksum`` – provides a checksum file
  that lacks an entry for the requested URL and expects the same
  ``RuntimeError``.

The tests deliberately avoid performing a real network download; they
monkey‑patch ``requests.get`` to raise an exception or return a mock
response.  This keeps the CI fast while still exercising the guard
logic.
"""

import builtins
from pathlib import Path
from unittest import mock

import pytest

from code.acquire import download_metabolomics

# ----------------------------------------------------------------------
# Helper fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def checksum_file(tmp_path: Path):
    """
    Create a temporary ``checksums.txt`` file under the project's data
    directory.  The fixture writes a single correct entry for a dummy
    URL and returns the path.  Tests can modify or delete the file to
    trigger error conditions.
    """
    checksums_dir = Path(__file__).resolve().parents[2] / "data" / "checksums"
    checksums_dir.mkdir(parents=True, exist_ok=True)
    file_path = checksums_dir / "checksums.txt"
    # Write a placeholder entry; the hash does not need to match anything
    # because the HTTP request will be mocked to fail before checksum
    # verification is reached.
    file_path.write_text("dummyhash  https://example.com/dummy.tsv\n")
    return file_path

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_metabolomics_missing_file(monkeypatch, tmp_path: Path):
    """
    Simulate a network failure (e.g., 404) and verify that the function
    raises the required ``RuntimeError`` with the exact FR‑008 message.
    """
    # Mock ``requests.get`` to return a response with status_code != 200
    mock_response = mock.Mock()
    mock_response.status_code = 404
    mock_response.iter_content = mock.Mock(return_value=[])

    monkeypatch.setattr("code.acquire.requests.get", lambda *args, **kwargs: mock_response)

    url = "https://example.com/missing.tsv"
    out_file = tmp_path / "missing.tsv"

    with pytest.raises(RuntimeError) as excinfo:
        download_metabolomics(url, out_file)
    assert str(excinfo.value) == "Metabolomics data unavailable – aborting per FR-008"


def test_metabolomics_missing_checksum(monkeypatch, tmp_path: Path, checksum_file: Path):
    """
    Remove the entry for the target URL from ``checksums.txt`` and ensure
    that ``download_metabolomics`` raises the required ``RuntimeError``.
    """
    # Ensure the checksum file exists but does NOT contain the target URL.
    # The file already contains a dummy entry for a different URL.

    # Mock a successful HTTP response with some content.
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.iter_content = lambda chunk_size: [b"dummy data"]

    monkeypatch.setattr("code.acquire.requests.get", lambda *args, **kwargs: mock_response)

    url = "https://example.com/unknown.tsv"
    out_file = tmp_path / "unknown.tsv"

    with pytest.raises(RuntimeError) as excinfo:
        download_metabolomics(url, out_file)
    assert str(excinfo.value) == "Metabolomics data unavailable – aborting per FR-008"


# The module is deliberately lightweight; no additional tests are needed
# for the successful download path because that would require a real
# network call, which is outside the scope of unit testing in CI.