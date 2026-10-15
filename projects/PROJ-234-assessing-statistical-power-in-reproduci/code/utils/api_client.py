"""
utils/api_client.py
-------------------

Thin wrapper around the OpenML REST API with exponential‑backoff retry
for HTTP 429 responses.  Provides a small class ``OpenMLClient`` and a
convenience function ``fetch_top_classification_datasets`` used by the
ingestion script.
"""

import time
import logging
from typing import List, Dict, Any

import openml
from openml import config as openml_config

logger = logging.getLogger(__name__)

class OpenMLClient:
    """
    Minimal client for fetching dataset listings from OpenML.

    Parameters
    ----------
    max_retries : int, optional
        Maximum number of retries for HTTP 429 responses (default 3).
    initial_delay : float, optional
        Initial back‑off delay in seconds (default 1.0).
    max_delay : float, optional
        Maximum back‑off delay in seconds (default 30.0).
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
    ) -> None:
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay

    def _request_with_backoff(self, func, *args, **kwargs):
        delay = self.initial_delay
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except openml.exceptions.OpenMLServerException as exc:
                # Detect rate‑limit (HTTP 429) via the exception message.
                if "429" in str(exc):
                    if attempt == self.max_retries:
                        logger.error("Maximum retries reached for OpenML request.")
                        raise
                    logger.warning(
                        f"OpenML rate limit encountered (attempt {attempt + 1}/{self.max_retries}). "
                        f"Backing off for {delay:.1f}s."
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, self.max_delay)
                else:
                    raise

    def fetch_top_classification_datasets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve the most‑downloaded classification datasets from OpenML.

        Returns a list of dictionaries, each representing a dataset entry.
        """
        # Ensure OpenML uses a writable cache (handled by the ingestion script,
        # but we keep the safety net here as well).
        openml_cache_dir = openml_config.cache_directory
        if not openml_cache_dir:
            openml_config.cache_directory = "openml_cache"

        def _list():
            return openml.datasets.list_datasets(output_format="dataframe")

        df = self._request_with_backoff(_list)

        # Keep only classification datasets.
        if "type" in df.columns:
            df = df[df["type"] == "Supervised Classification"]
        else:
            logger.warning("OpenML dataset list missing 'type' column; using full list.")

        # Sort by download count and limit.
        if "download_count" in df.columns:
            df = df.sort_values(by="download_count", ascending=False).head(limit)
        else:
            logger.warning("OpenML dataset list missing 'download_count' column; using unsorted list.")
            df = df.head(limit)

        return df.to_dict(orient="records")

# Convenience function used by scripts that do not need a full client instance.
def fetch_top_classification_datasets(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Shortcut to fetch the top classification datasets without explicitly
    constructing an ``OpenMLClient``.
    """
    client = OpenMLClient()
    return client.fetch_top_classification_datasets(limit=limit)