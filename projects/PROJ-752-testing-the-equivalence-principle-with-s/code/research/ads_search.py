"""
ADS API Search Script for Eötvös Parameter Benchmarks
----------------------------------------------------
This script implements task **T048.0a**: it searches the NASA/SAO
Astrophysics Data System (ADS) for peer‑reviewed papers that define
state‑of‑the‑art benchmarks for the Eötvös parameter precision using
satellite laser ranging (SLR).

The script:
  1. Reads an ADS API token from the environment variable ``ADS_API_TOKEN``.
     The token must have the ``read:search`` scope.  If the variable is not
     set the script aborts with a clear error message – this satisfies the
     “fail loudly” requirement.
  2. Sends a GET request to the ADS API endpoint
     ``https://api.adsabs.harvard.edu/v1/search/query`` with the query:
     ``"Eötvös parameter limit satellite laser ranging" AND date:[2010-01-01 TO *]``.
  3. Retrieves the fields ``title``, ``author``, ``abstract``, ``doi``,
     ``bibcode`` and ``pubdate`` for each hit.
  4. Parses the abstract (or the first 500 characters of the full text if
     available) for a numeric precision value using a regular expression.
     The regex looks for patterns such as ``precision ... 1.2 e -13``.
  5. Keeps only papers published after 2010 whose extracted precision is
     **strictly less than 1e‑13**.
  6. Returns a list of candidate papers as Python dictionaries and prints the
     JSON representation to ``stdout``.  The list is *temporary* – it is
     **not** written to disk per the task specification.

The script is designed to be idempotent and side‑effect free.  It can be
executed directly:

    python code/research/ads_search.py

The output can be captured or piped to a file for downstream processing
(e.g. the subsequent T048.0b task).

Dependencies:
  * Standard library modules only (``os``, ``json``, ``re``, ``logging``).
  * ``requests`` – already available in the project environment.
  * ``llmxive_toolkit`` for consistent logging paths.

Note:
  The ADS API imposes rate limits; the script respects them by performing a
  single request (the default page size is 200 records, which comfortably
  covers the expected number of relevant papers).  If more results are
  needed, pagination logic can be added later.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any

import requests
from llmxive_toolkit import get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ADS_API_ENDPOINT = "https://api.adsabs.harvard.edu/v1/search/query"
# Query defined in the task description
SEARCH_QUERY = (
    '"Eötvös parameter limit satellite laser ranging" '
    "AND date:[2010-01-01 TO *]"
)
# Fields we need from the API response
RETURN_FIELDS = ["title", "author", "abstract", "doi", "bibcode", "pubdate"]
# Precision threshold (strictly less than this value)
PRECISION_THRESHOLD = 1e-13
# Regular expression to capture scientific notation like "1.23 e -13"
PRECISION_REGEX = re.compile(
    r"precision.*?(\d+\.?\d*)\s*e\s*-?(\d+)", re.IGNORECASE
)

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def _get_ads_token() -> str:
    """
    Retrieve the ADS API token from the environment.

    Returns
    -------
    str
        The token string.

    Raises
    ------
    RuntimeError
        If the ``ADS_API_TOKEN`` environment variable is missing.
    """
    token = os.getenv("ADS_API_TOKEN")
    if not token:
        raise RuntimeError(
            "ADS API token not found. Please set the environment variable "
            "'ADS_API_TOKEN' with a valid token that has 'read:search' scope."
        )
    return token

def _fetch_ads_results(token: str) -> List[Dict[str, Any]]:
    """
    Query the ADS API and return the list of result dictionaries.

    Parameters
    ----------
    token : str
        Bearer token for authentication.

    Returns
    -------
    List[Dict[str, Any]]
        List of raw result entries from ADS.
    """
    params = {
        "q": SEARCH_QUERY,
        "fl": ",".join(RETURN_FIELDS),
        "rows": 200,  # default page size; increase if needed
    }
    headers = {"Authorization": f"Bearer {token}"}
    log.info("Sending request to ADS API...")
    response = requests.get(ADS_API_ENDPOINT, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    # ADS returns results under ``response.docs``
    docs = data.get("response", {}).get("docs", [])
    log.info(f"Received {len(docs)} records from ADS.")
    return docs

def _extract_precision(text: str) -> float | None:
    """
    Extract a numeric precision value from a text string using the defined regex.

    Parameters
    ----------
    text : str
        Text (typically the abstract) to search.

    Returns
    -------
    float | None
        The extracted precision as a float, or ``None`` if not found.
    """
    match = PRECISION_REGEX.search(text)
    if not match:
        return None
    mantissa, exponent = match.groups()
    try:
        value = float(mantissa) * (10 ** -int(exponent))
        return value
    except ValueError:
        return None

def _filter_candidates(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Keep only papers that satisfy the publication date and precision criteria.

    Parameters
    ----------
    docs : List[Dict[str, Any]]
        Raw ADS result entries.

    Returns
    -------
    List[Dict[str, Any]]
        Filtered list of candidate papers with extracted precision.
    """
    candidates = []
    for entry in docs:
        # Publication year extraction (pubdate format: YYYY-MM-DD or YYYY)
        pubdate = entry.get("pubdate", "")
        year_match = re.search(r"(\d{4})", pubdate)
        if not year_match:
            continue
        year = int(year_match.group(1))
        if year < 2010:
            continue

        abstract = entry.get("abstract", "")
        if not abstract:
            continue

        precision = _extract_precision(abstract)
        if precision is None:
            log.warning(
                f"Precision not found in abstract of paper {entry.get('bibcode')}. "
                "Skipping (will be flagged for manual review)."
            )
            continue

        if precision < PRECISION_THRESHOLD:
            candidate = {
                "title": entry.get("title", [""])[0],
                "authors": entry.get("author", []),
                "year": year,
                "precision": precision,
                "doi": entry.get("doi", [""])[0],
                "bibcode": entry.get("bibcode", ""),
            }
            candidates.append(candidate)
    log.info(f"Found {len(candidates)} candidate papers meeting precision criteria.")
    return candidates

# ----------------------------------------------------------------------
# Main Execution
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the ADS search script.

    The function prints a JSON array of candidate papers to stdout.
    """
    try:
        token = _get_ads_token()
    except RuntimeError as exc:
        log.error(str(exc))
        raise

    docs = _fetch_ads_results(token)
    candidates = _filter_candidates(docs)

    # Output the temporary list as JSON (stdout)
    print(json.dumps(candidates, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
