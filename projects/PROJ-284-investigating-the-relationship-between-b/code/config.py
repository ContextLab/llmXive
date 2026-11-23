"""
Configuration utilities for the project.

This file already existed in the repository; we only add a tiny
helper that returns a dictionary with HCP credentials (if any) so
that ``fetch_hcp_behavioral`` can use them for authenticated downloads.
The function is deliberately forgiving – if environment variables are
missing it returns an empty dict, causing the download to proceed
anonymously.
"""

from __future__ import annotations

import os
from typing import Dict

def get_hcp_credentials() -> Dict[str, str]:
    """
    Return a dict with ``access_key`` and ``secret_key`` for HCP S3 access.

    The credentials are read from the environment variables
    ``HCP_ACCESS_KEY`` and ``HCP_SECRET_KEY``.  If they are not set,
    an empty dict is returned and the download proceeds without
    authentication.
    """
    access_key = os.getenv("HCP_ACCESS_KEY")
    secret_key = os.getenv("HCP_SECRET_KEY")
    if access_key and secret_key:
        return {"access_key": access_key, "secret_key": secret_key}
    return {}