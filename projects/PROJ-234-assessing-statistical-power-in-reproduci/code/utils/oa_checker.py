"""
Simple Open‑Access checker.

Recognises a small whitelist of known OA domains and falls back to a
``HEAD`` request for other URLs.  All network‑related failures raise
``DataFetchError``.
"""
import re
from typing import Optional

import requests

class DataFetchError(Exception):
    """Raised when the OA check cannot be performed."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

# Pre‑compiled whitelist regexes – they match the domain part of the URL.
_OA_WHITELIST = [
    re.compile(r"^https?://(?:www\.)?arxiv\.org/"),
    re.compile(r"^https?://doi\.org/10\."),  # matches doi.org/10.xxx
    re.compile(r"^https?://(?:www\.)?pubmedcentral\.nih\.gov/"),
]

def _url_matches_whitelist(url: str) -> bool:
    """Return True if *url* matches any of the known OA patterns."""
    return any(pattern.search(url) for pattern in _OA_WHITELIST)

def is_open_access(url: str, *, timeout: float = 10.0) -> bool:
    """
    Determine whether a given URL points to an Open‑Access resource.

    The function first checks a hard‑coded whitelist of domains that are
    known to provide OA content.  If the URL is not on the whitelist a
    ``HEAD`` request is issued; the request is considered successful when
    the response is ``ok`` and the ``Content‑Type`` header indicates a
    textual document (e.g. ``text/html``).

    Parameters
    ----------
    url : str
        URL to test.
    timeout : float, optional
        Seconds to wait for the HEAD request.

    Returns
    -------
    bool
        ``True`` if the resource is OA, ``False`` otherwise.

    Raises
    ------
    DataFetchError
        If the network request fails.
    """
    # Fast path – known OA domains.
    if _url_matches_whitelist(url):
        return True

    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
    except Exception as exc:
        raise DataFetchError(f"Network error while checking OA status for {url}: {exc}")

    # ``ok`` means status code in the 200‑299 range.
    if not response.ok:
        # Treat non‑2xx as “not OA” rather than raising – the caller may
        # want to continue with a pay‑walled flag.
        return False

    # Look at the ``Content‑Type`` header.
    content_type = response.headers.get("Content-Type", "").lower()
    # Very permissive – any textual mime type is considered OA.
    return "text" in content_type or "html" in content_type
