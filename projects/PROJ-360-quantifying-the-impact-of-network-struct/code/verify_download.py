"""
Verify that at least a required number of CIF files have been downloaded.

This script is intended to be run after the `download.py` step. It checks the
number of ``*.cif`` files present in the designated directory (by default
``data/raw/cif``) and exits with a non‑zero status if fewer than the required
minimum (default 50) are found. The check is logged via the project's shared
logger obtained from ``llmxive_toolkit.get_logger``.
"""

import sys
import logging
from pathlib import Path
from llmxive_toolkit import paths, get_logger

DEFAULT_MIN = 50

def count_cif_files(directory: Path) -> int:
    """Return the number of ``*.cif`` files in *directory*."""
    return len(list(directory.glob("*.cif")))

def verify(directory: Path, min_required: int = DEFAULT_MIN) -> int:
    """
    Verify that *directory* contains at least *min_required* CIF files.

    Parameters
    ----------
    directory: Path
        Directory to scan for CIF files.
    min_required: int
        Minimum number of files required (default 50).

    Returns
    -------
    int
        The number of CIF files found.

    Raises
    ------
    RuntimeError
        If the count is lower than *min_required*.
    """
    logger = get_logger(__name__)
    logger.info(f"Checking CIF files in {directory}")
    count = count_cif_files(directory)
    logger.info(f"Found {count} CIF files")
    if count < min_required:
        logger.error(
            f"Insufficient CIF files: {count} found, {min_required} required."
        )
        raise RuntimeError(
            f"Only {count} CIF files found; at least {min_required} required."
        )
    logger.info("CIF file count verification passed.")
    return count

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify that the expected number of CIF files have been downloaded."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=str(paths.data("raw", "cif")),
        help="Directory containing CIF files (default: data/raw/cif)",
    )
    parser.add_argument(
        "--min",
        type=int,
        default=DEFAULT_MIN,
        help="Minimum number of CIF files required (default: 50)",
    )
    args = parser.parse_args()

    try:
        count = verify(Path(args.dir), args.min)
        print(f"Verification succeeded: {count} CIF files present.")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
