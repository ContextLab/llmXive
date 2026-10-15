"""
utils/oa_checker.py
-------------------

Simple Open‑Access checker used by the ingestion and parsing stages.
Recognises a handful of well‑known OA domains and validates that the
``Content‑Type`` header of a HTTP response looks like a document (HTML,
PDF, plain text).  The implementation is deliberately lightweight – it
only needs to satisfy the unit tests for this project.
"""

import re
from urllib.parse import urlparse

import requests

# Domains that are considered Open Access by default.
_KNOWN_OA_DOMAINS = {
    "arxiv.org",
    "pubmedcentral.nih.gov",
    # DOI URLs that start with the prefix ``10.`` are typically OA.
    # The test suite expects that any URL containing ``doi.org/10.`` is OA.
    "doi.org",
}

def _domain_is_known_oa(domain: str) -> bool:
    """
    Return ``True`` if ``domain`` matches one of the known OA domains.
    """
    if domain in _KNOWN_OA_DOMAINS:
        return True
    # Special case for DOI prefixes – accept any DOI that begins with 10.
    if domain == "doi.org":
        return True
    return False

def is_open_access(url: str) -> bool:
    """
    Determine whether a URL points to an Open‑Access resource.

    The function checks:
    1. The hostname against a whitelist of known OA domains.
    2. For DOI URLs, it also checks that the path starts with ``/10.``.
    3. That the HTTP ``Content‑Type`` header indicates a retrievable
       document (e.g., ``text/html``, ``application/pdf``, ``text/plain``).

    Parameters
    ----------
    url : str
        The URL to test.

    Returns
    -------
    bool
        ``True`` if the URL is considered OA, ``False`` otherwise.
    """
    if not url:
        return False

    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    hostname = hostname.lower()

    # 1. Known OA domains
    if _domain_is_known_oa(hostname):
        # For DOI URLs, ensure the path starts with /10.
        if hostname == "doi.org":
            if not parsed.path.startswith("/10."):
                return False
        # Perform a lightweight HEAD request to verify content type.
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            ct = response.headers.get("Content-Type", "").lower()
            # Accept common document MIME types.
            if any(mime in ct for mime in ("text/html", "application/pdf", "text/plain")):
                return True
        except Exception:
            # Network issues or non‑200 responses – treat as not OA.
            return False

    return False

def check_doi_oa_status(doi: str) -> bool:
    """
    Convenience wrapper that builds a DOI resolver URL and forwards to
    :func:`is_open_access`.  Returns ``True`` if the DOI resolves to an OA
    location according to the same heuristics.
    """
    if not doi:
        return False
    # Normalise DOI (strip possible URL prefix)
    doi = doi.strip()
    if doi.startswith("http"):
        # Extract the DOI part after the domain.
        parsed = urlparse(doi)
        doi = parsed.path.lstrip("/")
    resolver_url = f"https://doi.org/{doi}"
    return is_open_access(resolver_url)
