"""
fetch_cochrane_data.py

Utility script to download a Cochrane meta‑analysis CSV dataset.
It provides:
  * ``load_jackson_2010_base_data`` – fetches the CSV from a URL and returns a list of dict rows.
  * ``validate_data_structure`` – checks that the required columns are present.
  * ``save_to_csv`` – writes a list‑of‑dicts to a CSV file.
  * ``main`` – CLI entry point used by the test‑suite.

The script follows the contract required by task **T001a**:
  * If the URL cannot be reached, ``load_jackson_2010_base_data`` raises
    ``FileNotFoundError``.
  * ``main`` returns exit code ``0`` on success and ``1`` on any failure,
    ensuring that a CI step will fail when the CSV is inaccessible.
"""

from __future__ import annotations

import argparse
import csv
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Dict, Any

REQUIRED_COLUMNS = {"study_id", "effect", "se", "n"}

def load_jackson_2010_base_data(url: str) -> List[Dict[str, Any]]:
    """
    Fetch the Jackson et al. (2010) base dataset CSV from ``url`` and return it
    as a list of dictionaries (one per row).

    Raises
    ------
    FileNotFoundError
        If the URL cannot be opened or the HTTP response code is not 200.
    RuntimeError
        If the response cannot be decoded as CSV.
    """
    try:
        with urllib.request.urlopen(url) as response:
            # ``urlopen`` will raise URLError (including HTTPError) for network
            # problems or non‑200 status codes.
            raw_bytes = response.read()
    except urllib.error.URLError as exc:
        # Convert any URL‑related error into the required FileNotFoundError.
        raise FileNotFoundError(f"Unable to fetch CSV from {url}: {exc}") from exc

    try:
        # Decode as UTF‑8; if this fails we treat it as a runtime error.
        text = raw_bytes.decode("utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed to decode CSV content from {url}") from exc

    # Use csv.DictReader to parse the CSV text.
    lines = text.splitlines()
    reader = csv.DictReader(lines)
    data = [dict(row) for row in reader]
    return data

def validate_data_structure(data: List[Dict[str, Any]]) -> bool:
    """
    Validate that each row in ``data`` contains the required columns for a
    Cochrane meta‑analysis base dataset.

    Returns
    -------
    bool
        ``True`` if all rows contain the required columns; ``False`` otherwise.
    """
    for row in data:
        if not REQUIRED_COLUMNS.issubset(row.keys()):
            return False
    return True

def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write ``data`` (a list of dictionaries) to ``output_path`` as a CSV file.
    The header order follows the keys of the first row; all rows must contain
    the same columns.

    Parameters
    ----------
    data : List[Dict[str, Any]]
        Rows to write.
    output_path : str
        Destination file path.
    """
    if not data:
        raise ValueError("No data provided to save_to_csv")
    # Ensure the parent directory exists.
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(data[0].keys())
    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def main() -> int:
    """
    CLI wrapper that downloads the base CSV from a URL and saves it to a
    user‑specified location.

    Returns
    -------
    int
        Exit code (0 on success, non‑zero on failure).
    """
    parser = argparse.ArgumentParser(
        description="Download a Cochrane meta‑analysis CSV and save it locally."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL to the CSV file.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path to write the downloaded CSV.",
    )
    args = parser.parse_args()

    try:
        data = load_jackson_2010_base_data(args.url)
    except FileNotFoundError as exc:
        # Propagate a non‑zero exit code for CI failure.
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    except Exception as exc:  # Catch any unexpected errors.
        sys.stderr.write(f"ERROR: Unexpected failure while fetching CSV: {exc}\n")
        return 1

    if not validate_data_structure(data):
        sys.stderr.write("ERROR: Downloaded CSV does not contain the required columns.\n")
        return 1

    try:
        save_to_csv(data, args.out)
    except Exception as exc:
        sys.stderr.write(f"ERROR: Failed to write CSV to {args.out}: {exc}\n")
        return 1

    # Success
    sys.stdout.write(f"CSV successfully downloaded and saved to {args.out}\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())