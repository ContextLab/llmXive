"""
Simple OpenNeuro client utilities.

This module provides a minimal wrapper around the public OpenNeuro REST API
to retrieve a list of dataset identifiers.  It is deliberately lightweight
and only depends on the ``requests`` library, which is available in the
execution environment.
"""

import logging
from typing import List

import requests
from llmxive_toolkit import get_logger

# Public logger – other modules can configure the root logger as needed.
log = get_logger(__name__)

# Base URL for the OpenNeuro v1 API – returns a JSON list of datasets.
_API_URL = "https://openneuro.org/api/v1/datasets"

def list_datasets(limit: int = 1000) -> List[str]:
    """
    Return a list of dataset IDs available on OpenNeuro.

    Parameters
    ----------
    limit : int, optional
        Maximum number of datasets to retrieve from the API.  The OpenNeuro
        endpoint caps the number of results; ``limit`` is passed as a query
        parameter.

    Returns
    -------
    List[str]
        Dataset identifiers such as ``'ds000001'``.
    """
    try:
        response = requests.get(_API_URL, params={"limit": limit}, timeout=30)
        response.raise_for_status()
        data = response.json()
        # Expected format: a list of dicts each containing an ``id`` key.
        ids = [item["id"] for item in data if isinstance(item, dict) and "id" in item]
        log.info(f"Retrieved {len(ids)} dataset IDs from OpenNeuro.")
        return ids
    except Exception as exc:
        # Propagate the exception after logging – callers decide how to handle it.
        log.error(f"Failed to list datasets from OpenNeuro: {exc}")
        raise
