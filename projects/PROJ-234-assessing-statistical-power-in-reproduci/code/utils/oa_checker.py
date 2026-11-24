"""
Open‑Access checker utilities.
"""

import urllib.parse
from typing import Optional

import requests
from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Known OA domains – can be extended in the future
_KNOWN_OA_DOMAINS = {
    "arxiv.org",
    "doi.org",
    "pubmedcentral.nih.gov",
}


class DataFetchError(RuntimeError):
    """Raised when a network request fails for OA checking."""
    pass


def _is_known_oa_domain(url: str) -> bool:
    """Return True if the URL's netloc matches a known OA domain."""
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        # Some URLs include sub‑domains (e.g., www.arxiv.org)
        # Strip leading ``www.`` for matching
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return any(netloc == domain or netloc.endswith("." + domain) for domain in _KNOWN_OA_DOMAINS)
    except Exception as e:
        log.debug(f"Failed to parse URL {url}: {e}")
        return False


def is_open_access(url: str) -> bool:
    """
    Determine whether a URL points to an Open‑Access resource.

    The function first checks whether the domain is in the known OA list.
    If it is, a lightweight ``HEAD`` request is performed to verify that the
    ``Content‑Type`` header looks like a readable document (HTML or PDF).

    Parameters
    ----------
    url : str
        URL to examine.

    Returns
    -------
    bool
        ``True`` if the resource appears to be OA, ``False`` otherwise.
    """
    if not url:
        log.debug("Empty URL supplied to is_open_access – returning False")
        return False

    if not _is_known_oa_domain(url):
        log.debug(f"Domain of {url} not recognised as OA")
        return False

    try:
        # Use HEAD to minimise bandwidth; fall back to GET if HEAD not allowed
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code >= 400:
            log.debug(f"HEAD request returned status {response.status_code} for {url}")
            return False
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" in content_type or "application/pdf" in content_type:
            log.debug(f"URL {url} has OA content type {content_type}")
            return True
        else:
            log.debug(f"URL {url} content type {content_type} not recognised as OA")
            return False
    except requests.RequestException as e:
        # Network problems – treat as not OA but do not raise
        log.debug(f"Request exception while checking OA for {url}: {e}")
        return False
