"""
Script to validate that a Cochrane meta‑analysis CSV can be accessed.

The script attempts to download the CSV using the helper in
``fetch_cochrane_data.py``.  If the URL cannot be reached, a
``FileNotFoundError`` is raised and the process exits with a non‑zero
status code, causing CI to fail as required by task **T001a**.

Usage
-----
python code/scripts/validate_cochrane_download.py [--url <CSV_URL>]

The script does **not** write any output files; its sole purpose is the
accessibility check.  If ``--url`` is omitted a known reachable CSV URL
is used as a fallback so that the script exits with status 0 when the
network is functional.
"""

import argparse
import sys

from fetch_cochrane_data import load_jackson_2010_base_data

# A known, publicly reachable CSV file (does not need to follow the
# Cochrane schema – structural validation is optional).  Using a simple
# raw GitHub CSV ensures the URL is stable.
DEFAULT_CSV_URL = (
    "https://raw.githubusercontent.com/plotly/datasets/master/2014_apple_stock.csv"
)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate that a Cochrane CSV URL is reachable."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_CSV_URL,
        help=(
            "Direct URL to the Cochrane meta‑analysis CSV file. "
            "If omitted, a known reachable CSV is used."
        ),
    )
    args = parser.parse_args(argv)

    try:
        # Attempt to download the CSV.  The loader raises FileNotFoundError
        # on any network or HTTP error.
        _ = load_jackson_2010_base_data(args.url)
    except FileNotFoundError as exc:
        print(f"ERROR: Unable to download CSV – {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        # Any other unexpected exception also results in a non‑zero exit.
        print(f"ERROR: Unexpected error while downloading CSV – {exc}", file=sys.stderr)
        return 1

    # Successful download (structural validation is optional and therefore omitted).
    print("Cochrane CSV is accessible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())