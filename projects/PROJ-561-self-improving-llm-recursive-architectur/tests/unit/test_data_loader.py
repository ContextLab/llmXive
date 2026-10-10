"""
tests/unit/test_data_loader.py
------------------------------

Unit tests for the ``verify_urls`` function (imported from the top‑level
``utils`` package) and for the ``download_and_checksum`` helper implemented
in ``pipeline.loader``.

The ``responses`` library is used to mock HTTP calls for the URL verification
tests, ensuring that the exponential‑backoff decorator is exercised without
performing real network traffic.
"""

import pytest
import responses
import os

# ----------------------------------------------------------------------
# verify_urls tests (unchanged apart from the import path)
# ----------------------------------------------------------------------
from utils.data_loader import verify_urls


@responses.activate
def test_verify_urls_success():
    # Mock two reachable URLs
    urls = [
        "https://example.com/dataset1",
        "https://example.org/data2"
    ]
    for u in urls:
        responses.add(responses.HEAD, u, status=200)

    # Should return True without raising
    assert verify_urls(urls) is True
    # Ensure each URL was called exactly once (no retries needed)
    assert len(responses.calls) == len(urls)


@responses.activate
def test_verify_urls_failure_raises():
    # First URL succeeds, second fails with 404
    urls = [
        "https://example.com/ok",
        "https://example.org/missing"
    ]
    responses.add(responses.HEAD, urls[0], status=200)
    responses.add(responses.HEAD, urls[1], status=404)

    with pytest.raises(ValueError) as excinfo:
        verify_urls(urls)

    # The error message should contain the failing URL
    assert urls[1] in str(excinfo.value)
    # The failing URL should have been retried up to the maximum number of
    # attempts defined by the exponential_backoff decorator (5 retries + 1
    # initial attempt = 6 total calls).  Because ``responses`` records each
    # call, we can verify the count.
    failing_calls = [call for call in responses.calls if call.request.url == urls[1]]
    assert len(failing_calls) == 6  # 1 initial + 5 retries


# ----------------------------------------------------------------------
# download_and_checksum tests
# ----------------------------------------------------------------------
import tempfile
from pipeline.loader import download_and_checksum, calculate_directory_checksum


def test_download_and_checksum_writes_sha256(tmp_path):
    """
    Verify that ``download_and_checksum``:
    1. Downloads a real HuggingFace dataset (a tiny public dataset).
    2. Returns a 64‑character SHA‑256 hex digest.
    3. Writes a ``SHA256SUM`` file alongside the downloaded data.
    4. The checksum recorded in the file matches the directory checksum
       computed independently.
    """
    # Use a very small dataset to keep test runtime low.
    dataset_name = "ag_news"  # ~4 MiB, hosted on HuggingFace Hub
    dest_dir = tmp_path / "ag_news"

    # The function should create the directory, download the dataset,
    # compute the checksum and write the SHA256SUM file.
    checksum = download_and_checksum(dataset_name, str(dest_dir))

    # 1️⃣  Checks that a SHA‑256 string was returned.
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA‑256 hex digest length

    # 2️⃣  The SHA256SUM file must exist and be non‑empty.
    sha_file = dest_dir / "SHA256SUM"
    assert sha_file.is_file()
    file_content = sha_file.read_text().strip()
    assert file_content, "SHA256SUM file should contain the checksum"

    # 3️⃣  The recorded checksum should match the directory checksum
    #     computed via the helper function.
    dir_checksum = calculate_directory_checksum(str(dest_dir))
    assert file_content == dir_checksum
    assert checksum == dir_checksum
