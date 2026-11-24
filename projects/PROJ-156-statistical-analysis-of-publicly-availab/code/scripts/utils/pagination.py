"""
pagination.py

Reusable pagination helper for the Speedrun.com API.
Provides a generic `paginate_api` function that iterates over paginated API
endpoints, collects the ``data`` payload from each page, and returns a flat
list of all items.

The helper is deliberately lightweight and does not depend on any project-
specific globals except for a logger instance supplied by the caller.
"""

import time
from typing import Callable, List, Any

def paginate_api(
    fetch_page_func: Callable[[str, Any], dict],
    url_builder: Callable[[int], str],
    logger: Any,
    max_pages: int = 100,
    sleep_seconds: float = 0.5,
) -> List[dict]:
    """
    Generic pagination iterator.

    Parameters
    ----------
    fetch_page_func : Callable[[str, logger], dict]
        Function that fetches a single page given a URL. It must accept the
        URL string and a logger, and return the parsed JSON response as a
        dictionary.
    url_builder : Callable[[int], str]
        Function that builds the URL for a given page number (1‑based).
    logger : Any
        Logger instance used for informational messages.
    max_pages : int, optional
        Upper bound on the number of pages to request (default 100).
    sleep_seconds : float, optional
        Seconds to sleep between successive requests to respect API rate
        limits (default 0.5).

    Returns
    -------
    List[dict]
        Accumulated list of ``data`` items from all fetched pages.
    """
    all_items: List[dict] = []

    for page in range(1, max_pages + 1):
        url = url_builder(page)
        logger.info(f"Fetching page {page}")
        response = fetch_page_func(url, logger)

        # Extract the payload; the Speedrun.com API returns a dict with a
        # ``data`` key containing the list of items.
        page_items = response.get("data", [])
        if not page_items:
            # No more items – stop pagination.
            break

        all_items.extend(page_items)

        # Determine whether another page exists.
        pagination = response.get("pagination", {})
        if not pagination.get("has_next", False):
            break

        if sleep_seconds:
            time.sleep(sleep_seconds)

    return all_items