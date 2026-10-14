"""Data loader utility.

The original pipeline expects a ``data_loader.py`` script with a
``--prepare`` flag that creates the raw data directory.  Real
dataset fetching is handled elsewhere; this stub merely ensures the
directory hierarchy exists so that downstream steps succeed.
"""

import argparse
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare raw data folder.")
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Create the raw data directory (no dataset download).",
    )
    args = parser.parse_args()
    if args.prepare:
        raw_path = paths.data("raw")
        raw_path.mkdir(parents=True, exist_ok=True)
        log.info("Raw data directory prepared at %s", raw_path)

if __name__ == "__main__":
    main()
