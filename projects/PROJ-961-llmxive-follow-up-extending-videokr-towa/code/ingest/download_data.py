"""
Data download script for the open‑access TVQA dataset and its knowledge graph.
This script fetches:
  1. The TVQA training split (question‑answer pairs) via HuggingFace `datasets`.
  2. The accompanying video‑metadata split (e.g., video lengths).
  3. The TVQA knowledge‑graph JSON from the verified repo `llmxive/videoqa-kg`.
All files are written under `data/raw/` and SHA‑256 checksums are recorded in
`data/raw/checksums.json`.  Any failure aborts loudly with `DataUnavailableError`
– no synthetic fallback is performed.
"""
import csv
import json
import logging
import sys
from pathlib import Path

from datasets import load_dataset  # pip‑install datasets
from huggingface_hub import hf_hub_download  # pip‑install huggingface_hub

# Toolkit helpers for standardized project paths
from llmxive_toolkit import paths

# Local checksum helper
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
        for idx, record in enumerate(iterable):
            # Ensure the record is a plain dict (datasets may return DatasetDict)
            if not isinstance(record, dict):
                record = dict(record)
            if writer is None:
                # Determine column order from the first record
                fieldnames = list(record.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            # Convert any non‑serialisable values to strings
            safe_record = {k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                           for k, v in record.items()}
            writer.writerow(safe_record)


def _download_tvqa_train(raw_dir: Path) -> Path:
    """Download the TVQA training split (streaming) and write to CSV."""
    try:
        logger.info("Downloading TVQA training split (streaming)...")
        tvqa_stream = load_dataset("tvqa", split="train", streaming=True)
    except Exception as exc:
        raise DataUnavailableError("Failed to download TVQA training split.") from exc

    csv_path = raw_dir / "tvqa_train.csv"
    logger.info(f"Writing TVQA training data to {csv_path}")
    _write_csv_from_iterable(tvqa_stream, csv_path)
    return csv_path


def _download_tvqa_metadata(raw_dir: Path) -> Path:
    """
    Download the TVQA metadata split (non‑streaming) and write to
    `metadata/video_lengths.csv`.  The exact fields present in the split are
    written unchanged; typical columns include `video_id` and `duration`.
    """
    try:
        logger.info("Downloading TVQA metadata split (non‑streaming)...")
        metadata = load_dataset("tvqa", split="metadata", streaming=False)
    except Exception as exc:
        raise DataUnavailableError("Failed to download TVQA metadata split.") from exc

    metadata_dir = raw_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    csv_path = metadata_dir / "video_lengths.csv"
    logger.info(f"Writing TVQA metadata to {csv_path}")
    _write_csv_from_iterable(metadata, csv_path)
    return csv_path


def _download_knowledge_graph(raw_dir: Path) -> Path:
    """Download the TVQA knowledge‑graph JSON from the verified repo."""
    repo_id = "llmxive/videoqa-kg"
    filename = "knowledge_graph.json"
    try:
        logger.info(f"Downloading knowledge graph '{filename}' from repo '{repo_id}'.")
        cached_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(raw_dir),
            force_download=False,
            resume_download=True,
        )
    except Exception as exc:
        raise DataUnavailableError("Failed to download knowledge graph.") from exc

    target_path = raw_dir / filename
    # Move from HF cache to the project’s raw directory
    Path(cached_path).replace(target_path)
    logger.info(f"Knowledge graph saved to {target_path}")
    return target_path


def _write_checksums(files: list[Path], raw_dir: Path) -> None:
    """Compute SHA‑256 for each file and write a JSON manifest."""
    checksum_entries = []
    for file_path in files:
        checksum = compute_sha256(file_path)
        entry = {
            "path": str(file_path.relative_to(raw_dir).as_posix()),
            "sha256": checksum,
        }
        checksum_entries.append(entry)

    checksums_path = raw_dir / "checksums.json"
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksum_entries, f, indent=2)
    logger.info(f"Checksums written to {checksums_path}")


def main() -> None:
    """
    Orchestrates the download of TVQA data and the knowledge graph,
    then records SHA‑256 checksums for reproducibility.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    downloaded_files = []

    # 1. TVQA training data (streaming)
    tvqa_train_path = _download_tvqa_train(raw_dir)
    downloaded_files.append(tvqa_train_path)

    # 2. TVQA metadata (non‑streaming)
    metadata_path = _download_tvqa_metadata(raw_dir)
    downloaded_files.append(metadata_path)

    # 3. Knowledge graph
    kg_path = _download_knowledge_graph(raw_dir)
    downloaded_files.append(kg_path)

    # 4. Checksums
    _write_checksums(downloaded_files, raw_dir)


if __name__ == "__main__":
    try:
        main()
    except DataUnavailableError as e:
        logger.error(e)
        sys.exit(1)
