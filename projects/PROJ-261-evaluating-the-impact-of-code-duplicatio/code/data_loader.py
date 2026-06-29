"""
Data Loader for the Code Duplication Evaluation Project.

This script streams a subset of the `codeparrot/github-code` dataset from HuggingFace
using the `datasets` library in streaming mode, writes the sampled data to a CSV
file under ``data/raw/github-code-sample.csv`` and logs the process.

The implementation is deliberately tolerant of unexpected command‑line arguments
(e.g. comments added in quickstart scripts) by using ``parse_known_args``.
"""

import argparse
import csv
import hashlib
import logging
import os
import sys
from pathlib import Path

from datasets import load_dataset

# Local imports – these symbols are defined elsewhere in the project
from data_loader import (
    setup_logging,
    compute_file_checksum,
    stream_dataset,
    save_raw_data_to_csv,
    download_and_save_sample,
    load_raw_data,
)

# ----------------------------------------------------------------------
# Helper Functions (public API – retained for backward compatibility)
# ----------------------------------------------------------------------


def setup_logging(log_file: str = "data/logs/data_loader.log") -> logging.Logger:
    """Configure a module‑level logger.

    Parameters
    ----------
    log_file: str
        Path to the log file. The parent directory is created if missing.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger("data_loader")
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Return the checksum of ``file_path`` using the chosen hash algorithm."""
    hash_func = getattr(hashlib, algorithm)()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def stream_dataset(
    dataset_name: str,
    split: str = "train",
    streaming: bool = True,
    max_bytes: int = 500 * 1024 * 1024,
):
    """
    Stream the HuggingFace dataset and yield rows until ``max_bytes`` of
    ``content`` have been accumulated.

    Parameters
    ----------
    dataset_name: str
        Fully‑qualified dataset identifier on the Hub.
    split: str
        Which split to stream (default: ``train``).
    streaming: bool
        Whether to enable streaming mode (must be ``True`` for large datasets).
    max_bytes: int
        Approximate byte budget for the sample (default 500 MiB).

    Yields
    ------
    dict
        Raw dataset entry.
    """
    logger = logging.getLogger("data_loader")
    logger.info(f"Starting stream for dataset {dataset_name} (split={split})")
    ds = load_dataset(dataset_name, split=split, streaming=streaming)

    accumulated = 0
    for row in ds:
        # The dataset typically contains a ``content`` field with the source code.
        content = row.get("content") or row.get("text") or ""
        if isinstance(content, str):
            accumulated += len(content.encode("utf-8"))
        else:
            # If the field is not a string we skip size accounting.
            content = str(content)

        yield {"content": content, "path": row.get("path", "")}
        if accumulated >= max_bytes:
            logger.info(
                f"Reached byte budget ({max_bytes // (1024 * 1024)} MiB); stopping stream."
            )
            break


def save_raw_data_to_csv(
    rows,
    output_path: Path,
    fieldnames=("path", "content"),
):
    """
    Write streamed rows to a CSV file.

    Parameters
    ----------
    rows: iterable of dict
        Rows produced by :func:`stream_dataset`.
    output_path: Path
        Destination CSV file.
    fieldnames: tuple
        Column order for the CSV.
    """
    logger = logging.getLogger("data_loader")
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Ensure only the expected columns are written.
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    logger.info(f"Saved raw dataset to {output_path}")


def download_and_save_sample(
    output_path: Path,
    dataset_name: str = "codeparrot/github-code",
    max_bytes: int = 500 * 1024 * 1024,
):
    """
    High‑level helper used by the CLI: stream the dataset and persist a CSV sample.

    Parameters
    ----------
    output_path: Path
        Where the CSV should be written.
    dataset_name: str
        HuggingFace dataset identifier.
    max_bytes: int
        Approximate size of the sampled data.
    """
    logger = logging.getLogger("data_loader")
    rows = stream_dataset(
        dataset_name=dataset_name,
        split="train",
        streaming=True,
        max_bytes=max_bytes,
    )
    save_raw_data_to_csv(rows, output_path)


def load_raw_data(csv_path: Path):
    """
    Load the CSV produced by :func:`download_and_save_sample` into a list of dicts.
    """
    logger = logging.getLogger("data_loader")
    if not csv_path.is_file():
        logger.error(f"Raw data file not found: {csv_path}")
        raise FileNotFoundError(csv_path)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ----------------------------------------------------------------------
# CLI Entrypoint
# ----------------------------------------------------------------------


def main(argv=None):
    """
    Command‑line interface.

    The function is tolerant of unknown arguments (e.g. comments that appear
    after the script name in a quickstart script) by using ``parse_known_args``.
    """
    parser = argparse.ArgumentParser(
        description="Stream a subset of the codeparrot/github-code dataset to CSV."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/github-code-sample.csv"),
        help="Path to write the CSV sample.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Deprecated – kept for backward compatibility; ignored.",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="codeparrot/github-code",
        help="HuggingFace dataset identifier.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Dataset configuration (if applicable).",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Force streaming mode (default is True).",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="data/logs/data_loader.log",
        help="Path to the log file.",
    )

    # ``parse_known_args`` returns a tuple (known, unknown). We ignore unknown
    # arguments so that comments or stray tokens do not cause a failure.
    args, _ = parser.parse_known_args(argv)

    logger = setup_logging(args.log_file)

    try:
        output_path = args.output
        logger.info(f"Starting download → {output_path}")

        # ``max_bytes`` is the core budget; we keep the 500 MiB default.
        max_bytes = 500 * 1024 * 1024

        download_and_save_sample(
            output_path=output_path,
            dataset_name=args.dataset,
            max_bytes=max_bytes,
        )

        # Record checksum for downstream validation.
        checksum = compute_file_checksum(output_path)
        logger.info(f"Checksum (SHA256) for {output_path.name}: {checksum}")

    except Exception as exc:
        logger.exception("Download failed")
        sys.exit(2)


if __name__ == "__main__":
    main()
