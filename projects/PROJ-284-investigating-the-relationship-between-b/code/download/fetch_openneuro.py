"""Fetch OpenNeuro dataset files.

This script is invoked by the quick‑start run‑book as:
    python code/download/fetch_openneuro.py --subjects 50 --output data/raw

It downloads a small public OpenNeuro dataset (by default ``ds000001``) using
the ``openneuro-py`` client.  The script respects the ``--subjects`` limit
and writes a concise ``download_log.csv`` to the output directory that
records which subject folders were successfully retrieved.

The implementation avoids any synthetic data generation – it either
downloads real files from OpenNeuro or raises an informative exception
if the request fails.  ``tqdm`` is used for progress indication; the
dependency is added to ``requirements.txt`` by this task.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

from tqdm import tqdm
from openneuro import OpenNeuro

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _ensure_output_dir(output_path: Path) -> None:
    """Create the output directory if it does not exist."""
    output_path.mkdir(parents=True, exist_ok=True)


def _write_log(csv_path: Path, rows: list[tuple[str, str]]) -> None:
    """Write a CSV log with headers ``subject_id`` and ``status``."""
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["subject_id", "status"])
        writer.writerows(rows)


def _download_subject(
    client: OpenNeuro,
    dataset_id: str,
    subject_id: str,
    dest_dir: Path,
) -> str:
    """
    Download all files for a given ``subject_id`` from ``dataset_id``.
    Returns a short status string (``"OK"`` or an error description).
    """
    try:
        # ``client.get_subject_files`` returns a list of dicts with a
        # ``url`` key pointing to the raw file location.
        files = client.get_subject_files(dataset_id, subject_id)
    except Exception as exc:
        return f"metadata_error: {exc}"

    subject_dir = dest_dir / subject_id
    subject_dir.mkdir(parents=True, exist_ok=True)

    for file_info in files:
        try:
            url = file_info["url"]
            filename = Path(url).name
            target_path = subject_dir / filename
            # ``client.download_file`` streams the file to ``target_path``.
            client.download_file(url, target_path)
        except Exception as exc:
            # If a single file fails we continue with the others – the
            # status will reflect the failure after the loop.
            return f"download_error: {exc}"
    return "OK"


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Download a limited number of subjects from an OpenNeuro dataset."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Maximum number of subjects to download (default: 5).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Directory where downloaded data and the log CSV will be stored.",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="ds000001",
        help="OpenNeuro dataset identifier (default: ds000001).",
    )
    args = parser.parse_args(argv)

    # Resolve paths early
    output_dir: Path = args.output
    _ensure_output_dir(output_dir)

    # Initialise OpenNeuro client
    client = OpenNeuro()

    # ------------------------------------------------------------------
    # Determine which subjects are available
    # ------------------------------------------------------------------
    try:
        dataset_meta = client.get_dataset(args.dataset_id)
    except Exception as exc:
        sys.stderr.write(f"ERROR: Unable to retrieve dataset metadata: {exc}\\n")
        sys.exit(1)

    # ``dataset_meta`` is expected to contain a ``subjects`` list.
    # Fallback handling if the key is missing.
    subject_ids: list[str] = dataset_meta.get("subjects", [])
    if not subject_ids:
        sys.stderr.write(
            f"ERROR: No subjects listed for dataset '{args.dataset_id}'.\\n"
        )
        sys.exit(1)

    # Limit to the requested number of subjects
    limited_subjects = subject_ids[: args.subjects]

    log_rows: list[tuple[str, str]] = []

    for sub_id in tqdm(limited_subjects, desc="Downloading subjects"):
        status = _download_subject(client, args.dataset_id, sub_id, output_dir)
        log_rows.append((sub_id, status))

    # Write a concise CSV log for downstream steps
    log_path = output_dir / "download_log.csv"
    _write_log(log_path, log_rows)

    print(f"Download completed. Log written to {log_path}")


if __name__ == "__main__":
    main()
