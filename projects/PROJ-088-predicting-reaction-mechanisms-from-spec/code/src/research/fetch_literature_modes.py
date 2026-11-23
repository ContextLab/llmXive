"""
fetch_literature_modes.py
-------------------------

This script programmatically retrieves known functional group vibrational
frequencies (in cm⁻¹) from two public sources:

* NIST Chemistry WebBook – the "Characteristic Frequencies" page.
* SDBS (Spectral Database for Organic Compounds) – the IR characteristic
  frequencies page.

The collected data are written to
``data/reference/literature_vibrational_modes.json`` as a JSON list of
dictionaries with the following schema:

.. code-block:: json

    [
      {
        "source": "NIST" | "SDBS",
        "group": "<functional group description>",
        "frequency_cm1": "<frequency string, may contain ranges>"
      },
      ...
    ]

The script is intended to be invoked from the quick‑start pipeline:

``python -m src.research.fetch_literature_modes``

It deliberately raises on any network or parsing error – there is **no
synthetic fallback** – to satisfy the project's “real data only” policy.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logger setup
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants – URLs of the public resources
# ----------------------------------------------------------------------
NIST_URL = "https://webbook.nist.gov/chemistry/characteristic-frequencies/"
# The SDBS IR characteristic frequencies page (publicly accessible)
SDBS_URL = "https://sdbs.db.aist.go.jp/sdbs/cgi-bin/charfreq?type=IR"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _fetch_html(url: str) -> str:
    """Retrieve the raw HTML of *url*.

    Raises:
        requests.HTTPError: If the request fails (non‑2xx status).
    """
    log.info(f"Fetching HTML from {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text

def _parse_nist(html: str) -> List[Dict[str, str]]:
    """Parse the NIST characteristic‑frequency table.

    The page contains a single ``<table>`` with rows of the form:

        <td>Functional group</td><td>Frequency (cm⁻¹)</td>

    Returns a list of dicts with keys ``source``, ``group`` and
    ``frequency_cm1``.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ValueError("NIST page does not contain a table of frequencies")

    entries: List[Dict[str, str]] = []
    for row in table.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) != 2:
            continue  # skip header/footer rows
        group, freq = cols
        entries.append(
            {
                "source": "NIST",
                "group": group,
                "frequency_cm1": freq,
            }
        )
    if not entries:
        raise ValueError("No frequency entries parsed from NIST page")
    log.info(f"Parsed {len(entries)} NIST functional‑group entries")
    return entries

def _parse_sdbs(html: str) -> List[Dict[str, str]]:
    """Parse the SDBS IR characteristic‑frequency table.

    The SDBS page also contains a single ``<table>`` with three columns:
    * No., *Functional group*, *Frequency (cm⁻¹)*.  We ignore the first
    column and extract the latter two.

    Returns a list of dicts with the same keys as ``_parse_nist``.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise ValueError("SDBS page does not contain a table of frequencies")

    entries: List[Dict[str, str]] = []
    for row in table.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 3:
            continue  # skip header/footer rows
        # cols[0] is an index, cols[1] is the group, cols[2] is the frequency
        _, group, freq = cols[:3]
        entries.append(
            {
                "source": "SDBS",
                "group": group,
                "frequency_cm1": freq,
            }
        )
    if not entries:
        raise ValueError("No frequency entries parsed from SDBS page")
    log.info(f"Parsed {len(entries)} SDBS functional‑group entries")
    return entries

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """Fetch, parse, combine, and write the literature vibrational‑mode data."""
    # Fetch source HTML
    nist_html = _fetch_html(NIST_URL)
    sdbs_html = _fetch_html(SDBS_URL)

    # Parse each source
    nist_entries = _parse_nist(nist_html)
    sdbs_entries = _parse_sdbs(sdbs_html)

    # Combine
    combined = nist_entries + sdbs_entries

    # Output path – ``paths.data`` creates the parent directories automatically
    out_path: Path = paths.data("reference", "literature_vibrational_modes.json")
    log.info(f"Writing combined literature data to {out_path}")

    # Write JSON (pretty‑printed for readability)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    log.info(f"Successfully wrote {len(combined)} entries to {out_path}")

if __name__ == "__main__":
    # When executed as a script ``python -m src.research.fetch_literature_modes``,
    # ``__package__`` is ``src.research`` and the relative import works.
    main()
