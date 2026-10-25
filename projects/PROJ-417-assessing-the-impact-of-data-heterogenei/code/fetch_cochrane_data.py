"""
fetch_cochrane_data.py

This script downloads a public Cochrane meta‑analysis CSV dataset,
validates that it contains the required columns, and saves it to a
user‑specified location.  If the URL cannot be reached, a
``FileNotFoundError`` is raised so that the pipeline can abort with a
clear error message (as required by FR‑001 / T001a).

Usage:
    python code/fetch_cochrane_data.py --url <CSV_URL> --out <output_path>

The script is deliberately minimal and has no side‑effects beyond
writing the downloaded file when successful.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any
import urllib.request
import urllib.error

# Expected column names in the Cochrane CSV.
_REQUIRED_COLUMNS = {"study_id", "effect", "se", "n"}

def load_jackson_2010_base_data(url: str) -> List[Dict[str, Any]]:
    """
    Fetches the Jackson et al. (2010) base dataset from the supplied URL.

    Parameters
    ----------
    url: str
        Direct URL to the CSV file.

    Returns
    -------
    List[Dict[str, Any]]
        A list of dictionaries, one per row.

    Raises
    ------
    FileNotFoundError
        If the URL cannot be opened (network error, 404, etc.).
    RuntimeError
        If the response cannot be decoded as CSV.
    """
    try:
        with urllib.request.urlopen(url) as response:
            # ``response.read()`` returns ``bytes`` – decode as UTF‑8.
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise FileNotFoundError(f"Unable to download CSV – HTTP error {exc.code}: {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise FileNotFoundError(f"Unable to download CSV – URL error: {exc.reason}") from exc

    # Parse CSV content.
    try:
        reader = csv.DictReader(raw.splitlines())
        data = [dict(row) for row in reader]
    except Exception as exc:
        raise RuntimeError(f"Failed to parse CSV from {url}") from exc

    return data

def validate_data_structure(data: List[Dict[str, Any]]) -> bool:
    """
    Validates that the fetched data contains the required columns.

    Parameters
    ----------
    data: List[Dict[str, Any]]
        Parsed CSV rows.

    Returns
    -------
    bool
        ``True`` if all required columns are present in every row,
        ``False`` otherwise.
    """
    if not data:
        return False

    # Check column presence using the first row (all rows share the same header).
    header = set(data[0].keys())
    missing = _REQUIRED_COLUMNS - header
    if missing:
        return False

    # Ensure each required column has a non‑empty value.
    for row in data:
        for col in _REQUIRED_COLUMNS:
            if col not in row or row[col] == "":
                return False
    return True

def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Writes a list of dictionaries to ``output_path`` as a CSV file.

    Parameters
    ----------
    data: List[Dict[str, Any]]
        The data to write.
    output_path: str
        Destination file path.
    """
    if not data:
        raise ValueError("No data to write")

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download and validate a public Cochrane meta‑analysis CSV."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL to the CSV file containing the Cochrane dataset.",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path where the downloaded CSV should be saved.",
    )
    args = parser.parse_args()

    try:
        data = load_jackson_2010_base_data(args.url)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not validate_data_structure(data):
        print(
            "ERROR: Downloaded CSV does not contain the required columns "
            f"{sorted(_REQUIRED_COLUMNS)}.",
            file=sys.stderr,
        )
        return 1

    try:
        save_to_csv(data, args.out)
    except Exception as exc:
        print(f"ERROR while saving CSV: {exc}", file=sys.stderr)
        return 1

    print(f"Cochrane CSV successfully downloaded and saved to {args.out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())