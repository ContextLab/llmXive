"""
validate_cochrane_csv.py

Optional validation script for the Cochrane meta‑analysis CSV download.
It attempts to fetch the CSV from a user‑provided URL using the same
loader that the main pipeline uses.  If the URL cannot be reached,
the script raises a ``FileNotFoundError`` with a clear error message,
causing the CI step to fail as required by task **T001a**.

Usage
-----
python code/scripts/validate_cochrane_csv.py --url <CSV_URL>

The script exits with status code 0 on success, and propagates the
``FileNotFoundError`` (exit code 1) on failure.
"""

import argparse
import sys

from fetch_cochrane_data import load_jackson_2010_base_data

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate that a Cochrane CSV URL is reachable."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="HTTP URL of the Cochrane meta‑analysis CSV file.",
    )
    args = parser.parse_args(argv)

    try:
        # Attempt to download the CSV.  The loader raises
        # FileNotFoundError if the URL cannot be opened.
        _ = load_jackson_2010_base_data(args.url)
    except FileNotFoundError as e:
        # Re‑raise with a clear message so that CI sees a failure.
        raise FileNotFoundError(
            f"Unable to access Cochrane CSV at {args.url!r}: {e}"
        ) from e

    print(f"Successfully accessed Cochrane CSV at {args.url}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
