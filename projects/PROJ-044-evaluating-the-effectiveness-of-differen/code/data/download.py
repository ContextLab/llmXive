"""
FEMNIST Data Downloader using a lightweight approach.

This module downloads the FEMNIST dataset from the Hugging Face Hub
without requiring the heavy ``datasets`` library to be pre‑installed.
If the library is missing, it will be installed on‑the‑fly. The download
proceeds in streaming mode and writes a parquet file to
``data/raw/femnist.parquet`` together with a SHA‑256 checksum file.

The implementation respects the project constraints:
* Only the ``femnist`` dataset is supported – attempts to download
  ``shakespeare`` raise a ``ValueError`` with the mandated message.
* No synthetic fallback – any failure raises ``DataFetchError``.
* Real data is fetched from the public Hugging Face repository.
"""

import argparse
import hashlib
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants & configuration
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

SUPPORTED_DATASETS = {"femnist"}
EXCLUDED_DATASETS = {"shakespeare"}
EXCLUSION_MESSAGE = "Shakespeare excluded per plan.md Gap Analysis"

MAX_RETRIES = 3
# Number of records to materialise – a modest subset keeps the download fast
# while still providing real, verifiable data.
MAX_RECORDS = 200_000

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
class DataFetchError(Exception):
    """Raised when the dataset cannot be fetched or written."""


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def write_checksum(file_path: Path, checksum: str) -> Path:
    """Write a ``.sha256`` file next to ``file_path``."""
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    checksum_path.write_text(f"{checksum}  {file_path.name}\n")
    logger.info(f"Checksum written to %s", checksum_path)
    return checksum_path


# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
def _ensure_datasets_installed() -> None:
    """
    Import ``datasets``; if unavailable, install it via pip.

    The function retries the import after installation. Any failure
    after the retry propagates as ``ImportError``.
    """
    try:
        import datasets  # noqa: F401
    except ImportError:
        logger.info("The ``datasets`` package is missing – installing now...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets==2.19.0"])
        # Re‑import after installation
        import importlib

        importlib.import_module("datasets")


def download_femnist_streaming(output_dir: Path) -> Path:
    """
    Stream the FEMNIST training split, materialise a parquet file and
    generate its SHA‑256 checksum.

    Parameters
    ----------
    output_dir:
        Directory where ``femnist.parquet`` will be created.

    Returns
    -------
    Path to the parquet file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "femnist.parquet"

    # If the file already exists and the checksum matches, reuse it.
    checksum_path = parquet_path.with_suffix(parquet_path.suffix + ".sha256")
    if parquet_path.is_file() and checksum_path.is_file():
        stored = checksum_path.read_text().split()[0]
        current = compute_sha256(parquet_path)
        if stored == current:
            logger.info("Existing parquet file and checksum verified – skipping download.")
            return parquet_path
        else:
            logger.warning("Checksum mismatch – re‑downloading dataset.")
            parquet_path.unlink()
            checksum_path.unlink()

    logger.info("Starting streaming download of FEMNIST via the ``datasets`` library...")
    _ensure_datasets_installed()
    from datasets import load_dataset  # Imported after ensuring availability

    retry = 0
    while retry < MAX_RETRIES:
        try:
            # ``streaming=True`` ensures we never load the whole corpus into memory.
            ds = load_dataset(
                "femnist",
                split="train",
                streaming=True,
            )
            records = []
            for i, example in enumerate(ds):
                # ``user_id`` in the original dataset maps to ``client_id``.
                client_id = example.get("user_id")
                label = example.get("label")
                if client_id is None or label is None:
                    continue
                records.append({"client_id": client_id, "label": label})
                if (i + 1) % 10_000 == 0:
                    logger.info("Fetched %d records …", i + 1)
                if len(records) >= MAX_RECORDS:
                    logger.info(
                        "Reached MAX_RECORDS (%d) – stopping early for quick download.",
                        MAX_RECORDS,
                    )
                    break

            if not records:
                raise DataFetchError("No records retrieved from the streaming endpoint.")

            df = pd.DataFrame(records)
            logger.info("Writing %d records to %s", len(df), parquet_path)
            df.to_parquet(parquet_path, index=False)

            checksum = compute_sha256(parquet_path)
            write_checksum(parquet_path, checksum)

            logger.info("Download and materialisation complete.")
            return parquet_path

        except Exception as exc:
            retry += 1
            logger.error("Attempt %d failed: %s", retry, exc)
            if retry >= MAX_RETRIES:
                raise DataFetchError(f"Failed after {MAX_RETRIES} attempts.") from exc
            wait = 2 ** retry
            logger.info("Retrying in %d seconds …", wait)
            time.sleep(wait)

    # Should never be reached
    raise DataFetchError("Unexpected exit from download loop.")


def download_dataset(dataset_name: str, output_dir: Optional[Path] = None) -> Path:
    """
    Public entry point used by the CLI.

    Parameters
    ----------
    dataset_name:
        Name of the dataset to download. Only ``femnist`` is supported.
    output_dir:
        Destination directory; defaults to ``data/raw``.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR

    name = dataset_name.lower()
    if name in EXCLUDED_DATASETS:
        raise ValueError(EXCLUSION_MESSAGE)

    if name not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    if name == "femnist":
        return download_femnist_streaming(output_dir)

    raise ValueError(f"No handler for dataset: {dataset_name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download FEMNIST (or other supported) dataset."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset to download (default: femnist).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to store the downloaded files (default: data/raw).",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else DATA_RAW_DIR

    try:
        logger.info("Initiating download for dataset: %s", args.dataset)
        parquet_path = download_dataset(args.dataset, out_dir)
        logger.info("Dataset stored at %s", parquet_path)
        sys.exit(0)
    except ValueError as ve:
        logger.error("Configuration error: %s", ve)
        sys.exit(1)
    except DataFetchError as dfe:
        logger.error("Data fetch error: %s", dfe)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during download")
        sys.exit(1)


if __name__ == "__main__":
    main()