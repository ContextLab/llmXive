"""
Script to validate that a Cochrane meta‑analysis CSV can be accessed.

The script attempts to download the CSV using the helper in
``fetch_cochrane_data.py``.  If the URL cannot be reached, a
``FileNotFoundError`` is raised and the process exits with a non‑zero
status code, causing CI to fail as required by task **T001a**.

Usage
-----
python code/scripts/validate_cochrane_download.py --url <CSV_URL>

The script does **not** write any output files; its sole purpose is the
accessibility check.
"""

import argparse
import sys

from fetch_cochrane_data import load_jackson_2010_base_data, validate_data_structure


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate that a Cochrane CSV URL is reachable."
    )
    parser.add_argument(
        "--url",
        required=True,
        help="Direct URL to the Cochrane meta‑analysis CSV file.",
    )
    args = parser.parse_args(argv)

    try:
        # Attempt to download the CSV.  The loader raises FileNotFoundError
        # on any network or HTTP error.
        data = load_jackson_2010_base_data(args.url)
    except FileNotFoundError as exc:
        print(f"ERROR: Unable to download CSV – {exc}", file=sys.stderr)
        return 1

    # Optional structural validation – ensures the required columns exist.
    if not validate_data_structure(data):
        print("ERROR: Downloaded CSV does not contain the required columns.", file=sys.stderr)
        return 1

    print("Cochrane CSV is accessible and structurally valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
