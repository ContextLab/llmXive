"""
fetch_cochrane_data.py

Utility for downloading the public Jackson et al. (2010) Cochrane meta‑analysis
base dataset. The primary function ``load_jackson_2010_base_data`` fetches a
CSV from a given URL, parses it into a list of dictionaries and raises a
``FileNotFoundError`` when the URL cannot be reached or does not return a
successful HTTP response. This behaviour satisfies task **T001a**, which
requires the pipeline to abort with a clear error if the external CSV is
inaccessible.

The module also provides a simple schema validator and CSV writer used by
the pipeline's higher‑level scripts.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from typing import List, Dict, Any

import urllib.request
import urllib.error

__all__ = [
    "load_jackson_2010_base_data",
    "validate_data_structure",
    "save_to_csv",
    "main",
]

# ----------------------------------------------------------------------
# Core loader
# ----------------------------------------------------------------------
def load_jackson_2010_base_data(url: str) -> List[Dict[str, Any]]:
    """
    Fetch the Jackson et al. (2010) base dataset CSV from ``url`` and return
    it as a list of dictionaries (one per row).

    The function uses ``urllib.request.urlopen`` as a context manager to
    ensure the network connection is properly closed.  If the URL cannot be
    opened (network error, DNS failure, HTTP error, etc.) a
    ``FileNotFoundError`` is raised – this is the behaviour required by
    task **T001a**.

    Parameters
    ----------
    url: str
        Direct URL to the CSV file.

    Returns
    -------
    List[Dict[str, Any]]
        Parsed CSV rows.

    Raises
    ------
    FileNotFoundError
        If the URL cannot be accessed or the HTTP response code is not 200.
    RuntimeError
        If the response cannot be decoded as CSV.
    """
    try:
        with urllib.request.urlopen(url) as response:
            # ``urlopen`` returns an HTTPResponse‑like object with a ``status`` attribute.
            # Some older Python versions expose ``getcode()``; we handle both.
            status = getattr(response, "status", None) or getattr(response, "getcode", lambda: None)()
            if status is not None and status != 200:
                raise FileNotFoundError(f"Unable to fetch CSV, HTTP status {status}")

            # Read and decode the CSV content.
            raw_bytes = response.read()
            try:
                text = raw_bytes.decode("utf-8")
            except Exception as exc:
                raise RuntimeError(f"Failed to decode CSV content: {exc}") from exc

            # Parse CSV using ``csv.DictReader``.
            csv_file = io.StringIO(text)
            reader = csv.DictReader(csv_file)
            return list(reader)

    except urllib.error.HTTPError as http_err:
        # HTTPError is a subclass of URLError but carries an HTTP status code.
        raise FileNotFoundError(f"HTTP error while fetching CSV: {http_err.code}") from http_err
    except urllib.error.URLError as url_err:
        # Network‑level errors (e.g., DNS failure, refused connection).
        raise FileNotFoundError(f"URL could not be opened: {url_err.reason}") from url_err
    except Exception as exc:
        # Any other unexpected error should surface clearly.
        raise RuntimeError(f"Unexpected error while loading CSV: {exc}") from exc

# ----------------------------------------------------------------------
# Simple schema validator
# ----------------------------------------------------------------------
def validate_data_structure(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that each row in ``data`` contains the required columns for a
    Cochrane meta‑analysis base dataset.

    Required columns (as used throughout the pipeline):
        - ``study_id``
        - ``effect``
        - ``se``
        - ``n``

    Returns ``True`` if all rows contain these columns; otherwise ``False``.
    """
    required = {"study_id", "effect", "se", "n"}
    for row in data:
        if not required.issubset(row.keys()):
            return False
    return True

# ----------------------------------------------------------------------
# CSV writer helper
# ----------------------------------------------------------------------
def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write ``data`` (a list of dictionaries) to ``output_path`` as a CSV
    file.  The header order follows the keys of the first row; all rows
    must contain the same columns.

    Parameters
    ----------
    data: List[Dict[str, Any]]
        Rows to write.
    output_path: str
        Destination file path.
    """
    if not data:
        raise ValueError("No data provided to write_to_csv")

    # Ensure the parent directory exists.
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Use the keys from the first row as the header order.
    header = list(data[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    CLI wrapper that downloads the base CSV from a URL and saves it to a
    user‑specified location.

    Usage example::
        python fetch_cochrane_data.py \\
            --url https://example.com/cochrane_base.csv \\
            --out data/processed/base_template.csv

    Returns
    -------
    int
        Exit code (0 on success, non‑zero on failure).
    """
    parser = argparse.ArgumentParser(
        description="Download the public Jackson et al. (2010) Cochrane base dataset."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL to the CSV file containing the base dataset.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path where the downloaded CSV should be saved.",
    )
    args = parser.parse_args()

    try:
        data = load_jackson_2010_base_data(args.url)
    except FileNotFoundError as fnf_err:
        print(f"ERROR: {fnf_err}", file=sys.stderr)
        return 1
    except RuntimeError as run_err:
        print(f"ERROR: {run_err}", file=sys.stderr)
        return 1

    if not validate_data_structure(data):
        print("ERROR: Downloaded data does not contain the required columns.", file=sys.stderr)
        return 1

    try:
        save_to_csv(data, args.out)
    except Exception as exc:
        print(f"ERROR while writing CSV: {exc}", file=sys.stderr)
        return 1

    print(f"Successfully downloaded and saved base dataset to {args.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())