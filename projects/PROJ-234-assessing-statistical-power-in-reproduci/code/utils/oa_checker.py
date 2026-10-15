"""
utils/oa_checker.py
-------------------
Helper to decide whether a URL points to an Open‑Access (OA) resource.

The function recognises a small whitelist of well‑known OA domains and,
for any other URL, performs a lightweight ``HEAD`` request to inspect the
``Content‑Type`` header.  If the request fails or the content type is not
indicative of openly readable material, ``False`` is returned.

All failures raise :class:`DataFetchError` so that callers can treat the
situation uniformly.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

import requests

from .api_client import DataFetchError

__all__ = ["is_open_access"]

# Simple whitelist of domains that are known to provide OA content.
_OA_DOMAIN_PATTERNS = [
    re.compile(r"arxiv\.org", re.IGNORECASE),
    re.compile(r"doi\.org/10\.", re.IGNORECASE),
    re.compile(r"pubmedcentral\.nih\.gov", re.IGNORECASE),
]

def _matches_oa_domain(url: str) -> bool:
    """Return True if the URL contains a recognised OA domain."""
    hostname = urlparse(url).netloc
    for pat in _OA_DOMAIN_PATTERNS:
        if pat.search(hostname):
            return True
    return False

def is_open_access(url: str, *, timeout: float = 10.0) -> bool:
    """
    Determine whether ``url`` points to an Open‑Access resource.

    The check proceeds in two steps:
    1. If the hostname matches a known OA domain, ``True`` is returned
       immediately (no network request performed).
    2. Otherwise a ``HEAD`` request is issued.  If the request succeeds and
       the ``Content‑Type`` header indicates a readable format
       (``text/html`` or ``application/pdf``), the function returns ``True``.
       Any other content type or a failed request results in ``False``.

    Parameters
    ----------
    url:
        The URL to test.
    timeout:
        Seconds to wait for the ``HEAD`` request.

    Returns
    -------
    bool
        ``True`` if the resource appears to be OA, ``False`` otherwise.
    """
    if _matches_oa_domain(url):
        return True

    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
    except requests.RequestException as exc:
        # Network problems – treat as not OA but surface a clear error.
        raise DataFetchError(f"Failed to perform HEAD request for {url}") from exc

    # Some servers do not implement HEAD; fall back to GET with stream=False.
    if response.status_code == 405:  # Method Not Allowed
        try:
            response = requests.get(url, stream=False, timeout=timeout)
        except requests.RequestException as exc:
            raise DataFetchError(f"Failed GET fallback for {url}") from exc

    if not response.ok:
        return False

    ct = response.headers.get("Content-Type", "").lower()
    # Accept typical OA MIME types.
    if "text/html" in ct or "application/pdf" in ct:
        return True
    return False
