"""
utils/data_loader.py
--------------------
Utilities for pre‑flight data loading checks.

This module provides a function ``verify_urls`` that checks the reachability
of a list of URLs before any dataset download is attempted.  It uses the
``exponential_backoff`` decorator implemented in ``pipeline.loader`` (task
T005b) to satisfy FR‑011 – API calls are retried with an initial delay of
30 seconds and a maximum of 5 retries.  If any URL cannot be reached after
the retries, a ``ValueError`` is raised, causing the pipeline to fail fast.
"""

from typing import List

import requests

# The exponential back‑off decorator is defined in ``pipeline.loader``.
# Importing it here avoids a circular dependency because ``pipeline.loader``
# does not import anything from ``utils``.
from pipeline.loader import exponential_backoff


@exponential_backoff
def _head_request(url: str) -> requests.Response:
    """
    Perform a ``HEAD`` request to ``url`` with a short timeout.

    The ``exponential_backoff`` decorator will automatically retry the call
    on any exception (including network errors and non‑2xx HTTP responses).

    Args:
        url: The URL to probe.

    Returns:
        The ``requests.Response`` object if the request succeeds.

    Raises:
        requests.HTTPError: If the response status is not successful.
    """
    response = requests.head(url, timeout=5, allow_redirects=True)
    # ``raise_for_status`` will raise an HTTPError for 4xx/5xx codes.
    response.raise_for_status()
    return response


def verify_urls(urls: List[str]) -> bool:
    """
    Verify that all URLs in ``urls`` are reachable.

    The function iterates over the supplied URLs and performs a ``HEAD``
    request for each, using exponential back‑off to handle transient failures
    (e.g., rate‑limits or temporary network issues).  If any URL remains
    unreachable after the maximum number of retries, a ``ValueError`` is raised
    with a clear message indicating which URL failed.

    Args:
        urls: List of URL strings to verify.

    Returns:
        ``True`` if every URL responded successfully.

    Raises:
        ValueError: If any URL is unreachable after retries.
    """
    for url in urls:
        try:
            _head_request(url)
        except Exception as exc:
            # Wrap the original exception to provide context while preserving
            # the traceback for debugging.
            raise ValueError(f"Unable to reach URL: {url}") from exc
    return True
