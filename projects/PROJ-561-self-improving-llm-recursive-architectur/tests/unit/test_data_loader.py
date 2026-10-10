"""
tests/unit/test_data_loader.py
------------------------------

Unit tests for the ``verify_urls`` function implemented in
``utils/data_loader.py``.  The tests use the ``responses`` library to mock
HTTP requests, ensuring that the back‑off logic is exercised without performing
real network calls.

The test suite covers:
  * Successful verification of reachable URLs.
  * Proper raising of ``ValueError`` when a URL returns a non‑2xx status.
  * Propagation of the back‑off retries (the mock records how many times the
    request was attempted).
"""

import pytest
import responses

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
    # Note: The decorator retries on any exception, including the HTTPError
    # raised by ``raise_for_status``.
    failing_calls = [call for call in responses.calls if call.request.url == urls[1]]
    assert len(failing_calls) == 6  # 1 initial + 5 retries