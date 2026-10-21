"""
Robust data‑download script for the open‑access TVQA dataset.

This script performs the following steps:
  1. Download the TVQA training split (streaming) and write it as a CSV.
  2. Download the TVQA metadata split (non‑streaming) and write it as a CSV.
  3. Download the bundled knowledge‑graph JSON from the verified repo
     ``llmxive/videoqa-kg``.
  4. Compute SHA‑256 checksums for every downloaded file and write them to
     ``data/raw/checksums.json``.

Any failure aborts loudly with ``DataUnavailableError`` – no synthetic fallback
is performed.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

# External dependencies
from datasets import load_dataset as hf_load_dataset
from huggingface_hub import hf_hub_download

# Toolkit helpers for standardized project paths
from llmxive_toolkit import paths
from utils.config import ensure_dir

# Local checksum helper (re‑exported for the tests)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ingest.checksum import compute_sha256  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class DataUnavailableError(RuntimeError):
    """Raised when any required dataset or file cannot be fetched."""


def _write_csv_from_iterable(iterable, output_path: Path) -> None:
    """
    Write an iterable of dictionaries to a CSV file.
    The first element determines the header order.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = None
        for record in iterable:
            # Ensure the record is a plain dict (datasets may return Dataset objects)
            if not isinstance(record, dict):
                record = dict(record)
            if writer is None:
                fieldnames = list(record.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            # Convert non‑primitive values to strings to keep CSV well‑formed
            safe_record = {
                k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                for k, v in record.items()
            }
            writer.writerow(safe_record)


def download_tvqa_train(output_dir: Path) -> Path:
    """
    Download the TVQA training split (streaming) and write it as a CSV.
    Returns the path to the created CSV file.
    """
    logger.info("Downloading TVQA training split (streaming)...")
    try:
        tvqa_stream = hf_load_dataset("tvqa", split="train", streaming=True)
    except Exception as exc:
        raise DataUnavailableError("Failed to download TVQA training split.") from exc

    csv_path = output_dir / "tvqa_train.csv"
    logger.info(f"Writing TVQA training data to CSV at {csv_path}")
    _write_csv_from_iterable(tvqa_stream, csv_path)
    return csv_path


def download_tvqa_metadata(output_dir: Path) -> Path:
    """
    Download the TVQA metadata split (non‑streaming) and write it as a CSV.
    Returns the path to the created metadata CSV file.
    """
    logger.info("Downloading TVQA metadata split (non‑streaming)...")
    try:
        metadata = hf_load_dataset("tvqa", split="metadata", streaming=False)
    except Exception as exc:
        raise DataUnavailableError("Failed to download TVQA metadata split.") from exc

    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    metadata_csv_path = metadata_dir / "video_lengths.csv"
    logger.info(f"Writing TVQA metadata to {metadata_csv_path}")
    _write_csv_from_iterable(metadata, metadata_csv_path)
    return metadata_csv_path


def download_knowledge_graph(output_dir: Path) -> Path:
    """
    Download the TVQA knowledge‑graph JSON from the verified repo.
    Returns the path to the saved JSON file.
    """
    repo_id = "llmxive/videoqa-kg"
    filename = "knowledge_graph.json"
    logger.info(
        f"Downloading knowledge graph '{filename}' from repo '{repo_id}'."
    )
    try:
        cached_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(output_dir),
            force_download=False,
            resume_download=True,
        )
        target_path = output_dir / filename
        Path(cached_path).replace(target_path)
        logger.info(f"Knowledge graph saved to {target_path}")
        return target_path
    except Exception as hf_exc:
        raise DataUnavailableError("Failed to download knowledge graph.") from hf_exc


def verify_checksums(output_dir: Path) -> Tuple[bool, Dict[str, str]]:
    """
    Compute SHA‑256 checksums for every file in ``output_dir`` (excluding the
    checksum manifest itself) and write ``checksums.json``. Returns a tuple
    ``(success, checksum_dict)`` where ``checksum_dict`` maps relative file
    paths (POSIX) to their hex digests.
    """
    checksum_entries = {}
    for file_path in output_dir.rglob("*"):
        if file_path.is_file() and file_path.name != "checksums.json":
            checksum = compute_sha256(file_path)
            rel_path = file_path.relative_to(output_dir).as_posix()
            checksum_entries[rel_path] = checksum

    checksums_path = output_dir / "checksums.json"
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(
            [
                {"path": p, "sha256": h}
                for p, h in checksum_entries.items()
            ],
            f,
            indent=2,
        )
    logger.info(f"Checksums written to {checksums_path}")
    return True, checksum_entries


def main() -> None:
    """
    Orchestrates the download of TVQA data and the knowledge graph,
    then records SHA‑256 checksums for reproducibility.
    """
    # The raw data folder is ``data/raw`` according to the project specification.
    raw_dir = paths.data("raw")
    ensure_dir(raw_dir)

    # 1. TVQA training data
    train_csv_path = download_tvqa_train(raw_dir)

    # 2. TVQA metadata
    metadata_csv_path = download_tvqa_metadata(raw_dir)

    # 3. Knowledge graph
    kg_path = download_knowledge_graph(raw_dir)

    # 4. Checksums
    verify_checksums(raw_dir)


if __name__ == "__main__":
    try:
        main()
    except DataUnavailableError as e:
        logger.error(e)
        sys.exit(1)
