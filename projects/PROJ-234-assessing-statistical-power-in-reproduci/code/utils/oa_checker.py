"""
code/utils/oa_checker.py
-------------------------

Utilities for determining whether a resource (URL or DOI) is Open Access.

The original project required two public helpers:
  * ``is_open_access(url: str) -> bool`` – quick HEAD request check.
  * ``check_doi_oa_status(doi: str) -> dict`` – richer Crossref lookup.

The test suite (``tests/unit/test_utils_refactor.py``) imports both symbols.
The original implementation only provided ``is_open_access`` which caused an
import error.  This file now implements **both** helpers while keeping the
original behaviour unchanged.
"""

import logging
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)

def is_open_access(url: str) -> bool:
    """
    Perform a lightweight HEAD request to determine if a URL points to an
    openly accessible resource.

    The function returns ``True`` when:
      * the request succeeds (status code < 400)
      * the ``Content‑Type`` header suggests a PDF, HTML or plain‑text
        document (common OA formats)

    Any exception (network error, timeout, etc.) results in ``False``.
    """
    if not url:
        return False
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        if response.status_code >= 400:
            return False
        ct = response.headers.get("Content-Type", "").lower()
        # Accept typical OA mime types
        return any(
            mime in ct for mime in ("application/pdf", "text/html", "text/plain")
        )
    except Exception as exc:  # pragma: no cover – exercised via mocks in tests
        logger.debug(f"OA check failed for {url}: {exc}")
        return False

def check_doi_oa_status(doi: str) -> Dict[str, Any]:
    """
    Query the Crossref API for a DOI and determine whether the work is Open
    Access.  The returned dictionary mirrors the expectations of the unit
    tests:

    {
        "is_open": bool,
        "license": Optional[str]  # URL of the OA licence if known
    }

    If the DOI cannot be resolved or the request fails, ``is_open`` is
    ``False`` and ``license`` is ``None``.
    """
    result: Dict[str, Any] = {"is_open": False, "license": None}
    if not doi:
        return result

    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        message = data.get("message", {})

        # Crossref provides a ``license`` list; we consider OA if any entry
        # contains a URL that includes a known open licence identifier.
        licenses = message.get("license", [])
        for lic in licenses:
            lic_url = lic.get("URL", "")
            if lic_url:
                result["license"] = lic_url
                # Simple heuristic: if the URL contains "creativecommons" or
                # ends with ".org/licenses/", we treat it as OA.
                if "creativecommons.org" in lic_url.lower() or "open" in lic_url.lower():
                    result["is_open"] = True
                    break

        # Some records expose ``type`` or ``published_print`` but not a licence.
        # As a fallback, if the DOI resolves to a URL that ends with ".pdf"
        # we assume OA (very permissive heuristic).
        if not result["is_open"]:
            link = message.get("URL", "")
            if isinstance(link, str) and link.lower().endswith(".pdf"):
                result["is_open"] = True
                result["license"] = link

    except Exception as exc:  # pragma: no cover – exercised via mocks in tests
        logger.debug(f"Failed to retrieve Crossref data for DOI {doi}: {exc}")

    return result