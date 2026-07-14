"""
url_security.py
----------------
Utility functions for hardening data download URLs.

This module provides:
* ``validate_download_url`` – Checks that a URL uses HTTPS and (optionally)
  belongs to an allowed whitelist of domains.
* ``secure_download`` – A thin wrapper around ``utils.retry_download`` that
  first validates the URL and then performs a retry‑enabled download with
  SSL verification.

The functions are deliberately lightweight and depend only on the Python
standard library and the existing project utilities so that they can be
imported from any part of the code base (e.g. ``data_ingestion.py``) without
introducing new third‑party dependencies.
"""

import logging
from typing import List, Optional
from urllib.parse import urlparse

from config import get_config
from utils import retry_download

logger = logging.getLogger(__name__)

def _default_allowed_domains() -> List[str]:
    """
    Retrieve the list of allowed download domains from the project
    configuration.  If the configuration does not specify a whitelist,
    fall back to a sensible default that includes the known Planck and
    BICEP/Keck data hosts.
    """
    cfg = get_config()
    # The config may contain a key ``ALLOWED_DOWNLOAD_DOMAINS``; if not,
    # we use a hard‑coded safe default.
    return cfg.get(
        "ALLOWED_DOWNLOAD_DOMAINS",
        ["planck.gsfc.nasa.gov", "bicepkeck.org"],
    )

def validate_download_url(
    url: str, allowed_domains: Optional[List[str]] = None
) -> str:
    """
    Validate that a download URL is safe to use.

    The validation steps are:

    1. The URL must be a non‑empty string.
    2. The scheme must be ``https`` (to enforce transport‑level encryption).
    3. The network location (domain) must be present in the whitelist of
       allowed domains.  If ``allowed_domains`` is ``None`` the whitelist
       is obtained from the project configuration via ``_default_allowed_domains``.

    Parameters
    ----------
    url: str
        The URL to validate.
    allowed_domains: list[str] | None
        Optional explicit whitelist; if omitted the project config is used.

    Returns
    -------
    str
        The original URL (unchanged) if validation succeeds.

    Raises
    ------
    ValueError
        If any of the validation checks fail.
    """
    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a non‑empty string.")

    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        raise ValueError(f"Insecure URL scheme '{parsed.scheme}'. Only HTTPS is allowed.")

    domain = parsed.hostname
    if not domain:
        raise ValueError("URL does not contain a valid hostname.")

    whitelist = allowed_domains if allowed_domains is not None else _default_allowed_domains()
    if domain.lower() not in (d.lower() for d in whitelist):
        raise ValueError(f"Domain '{domain}' is not in the allowed download whitelist.")

    logger.debug("Validated download URL: %s (domain %s)", url, domain)
    return url

def secure_download(
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    allowed_domains: Optional[List[str]] = None,
) -> bytes:
    """
    Perform a hardened download of a remote resource.

    This function first validates the URL using :func:`validate_download_url`
    and then delegates the actual data retrieval to ``utils.retry_download``,
    which implements exponential back‑off and retry logic.

    Parameters
    ----------
    url: str
        The HTTPS URL to download.
    max_retries: int
        Maximum number of retry attempts (passed through to ``retry_download``).
    base_delay: float
        Initial back‑off delay in seconds (passed through to ``retry_download``).
    allowed_domains: list[str] | None
        Optional explicit whitelist of domains.

    Returns
    -------
    bytes
        The raw payload returned by the HTTP request.

    Raises
    ------
    ValueError
        If the URL fails validation.
    requests.RequestException
        Propagated from ``retry_download`` if the download ultimately fails.
    """
    # Validate before any network activity.
    validated_url = validate_download_url(url, allowed_domains=allowed_domains)

    logger.info("Starting secure download of %s", validated_url)
    data = retry_download(validated_url, max_retries=max_retries, base_delay=base_delay)
    logger.info("Successfully downloaded %d bytes from %s", len(data), validated_url)
    return data

def main() -> None:
    """
    Simple command‑line entry point for manual testing.

    Usage:
        python -m code.url_security <URL>
    """
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m code.url_security <HTTPS_URL>")
        sys.exit(1)

    url = sys.argv[1]
    try:
        content = secure_download(url)
        print(f"Downloaded {len(content)} bytes from {url}")
    except Exception as exc:
        logger.error("Secure download failed: %s", exc)
        sys.exit(1)
