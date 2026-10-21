"""
Robust data‑download script for the open‑access TVQA dataset.

This script performs the following steps:
  1. Download the TVQA training split and write it as ``tvqa_train.csv`` under ``data/raw``.
  2. Derive a ``metadata/video_lengths.csv`` file from the training split (video IDs + length seconds).
  3. Download the bundled knowledge‑graph JSON from the verified repo ``llmxive/videoqa-kg`` and write it as ``knowledge_graph.json``.
  4. Compute SHA‑256 checksums for every downloaded file and write them to ``checksums.json`` in the same directory.

Any failure aborts loudly with ``DataUnavailableError`` – no synthetic fallback is performed.
"""
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

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


# ----------------------------------------------------------------------
# Helper to load datasets with a clear error on failure.
# ----------------------------------------------------------------------
def _load_dataset(*args, **kwargs):
    """
    Wrapper around ``datasets.load_dataset`` that raises ``DataUnavailableError``
    if the import or the download fails.
    """
    try:
        from datasets import load_dataset as hf_load_dataset
        return hf_load_dataset(*args, **kwargs)
    except Exception as exc:  # pragma: no cover – exercised via tests
        raise DataUnavailableError(
            f"Failed to load dataset with args={args}, kwargs={kwargs}"
        ) from exc


# ----------------------------------------------------------------------
# Helper to write an iterable of dict‑like records to CSV.
# ----------------------------------------------------------------------
def _write_csv(iterable: Any, output_path: Path) -> None:
    """
    Write an iterable of dictionaries to a CSV file.
    The first record determines the header order.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = None
        for rec in iterable:
            # Ensure we have a plain dict
            if not isinstance(rec, dict):
                rec = dict(rec)
            if writer is None:
                fieldnames = list(rec.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            # Make sure values are CSV‑serialisable
            safe_rec = {
                k: (v if isinstance(v, (str, int, float, bool)) else str(v))
                for k, v in rec.items()
            }
            writer.writerow(safe_rec)


# ----------------------------------------------------------------------
# 1. TVQA training split – CSV
# ----------------------------------------------------------------------
def _download_tvqa_train(output_dir: Path) -> Path:
    """
    Download the TVQA training split and write it as ``tvqa_train.csv``.
    """
    logger.info("Downloading TVQA training split...")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "tvqa_train.csv"

    dataset = _load_dataset("tvqa", split="train", streaming=False)

    # ``datasets`` objects are iterable over dict‑like rows
    _write_csv(dataset, csv_path)
    logger.info(f"TVQA training CSV written to {csv_path}")
    return csv_path


# ----------------------------------------------------------------------
# 2. TVQA metadata – CSV (derived from the training split)
# ----------------------------------------------------------------------
def _download_tvqa_metadata(output_dir: Path) -> Path:
    """
    Derive a ``video_lengths.csv`` file from the TVQA training split.
    The CSV contains two columns: ``video_id`` and ``length_seconds``.
    """
    logger.info("Deriving TVQA metadata (video lengths)...")
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    csv_path = metadata_dir / "video_lengths.csv"

    # Load the same training split – it contains the required fields.
    dataset = _load_dataset("tvqa", split="train", streaming=False)

    video_lengths: Dict[str, float] = {}
    for rec in dataset:
        # TVQA records contain a ``video_id`` field and a ``duration`` field.
        # Some versions expose ``video_length_seconds`` – we handle both.
        video_id = rec.get("video_id") or rec.get("video")
        length = rec.get("duration") or rec.get(
            "video_length_seconds"
        ) or rec.get("video_length")
        if video_id is None or length is None:
            # If the required fields are missing, we cannot construct the metadata.
            raise DataUnavailableError(
                "Unable to extract video_id and length from TVQA records."
            )
        # Keep the first observed length for each video (they are constant per video).
        if video_id not in video_lengths:
            try:
                video_lengths[video_id] = float(length)
            except Exception as exc:
                raise DataUnavailableError(
                    f"Invalid length value for video {video_id}: {length}"
                ) from exc

    # Write CSV
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["video_id", "length_seconds"])
        writer.writeheader()
        for vid, sec in sorted(video_lengths.items()):
            writer.writerow({"video_id": vid, "length_seconds": sec})

    logger.info(f"TVQA metadata CSV written to {csv_path}")
    return csv_path


# ----------------------------------------------------------------------
# 3. Knowledge‑graph JSON – HuggingFace Hub
# ----------------------------------------------------------------------
def _download_knowledge_graph(output_dir: Path) -> Path:
    """
    Download the knowledge‑graph JSON from the verified repo
    ``llmxive/videoqa-kg`` and write it as ``knowledge_graph.json``.
    """
    logger.info("Downloading knowledge graph from huggingface hub...")
    output_dir.mkdir(parents=True, exist_ok=True)
    kg_path = output_dir / "knowledge_graph.json"

    try:
        from huggingface_hub import hf_hub_download
    except Exception as exc:  # pragma: no cover – library missing
        raise DataUnavailableError(
            "huggingface_hub is required but not installed."
        ) from exc

    # The repo contains a single JSON file; we request the default filename.
    try:
        downloaded_path = hf_hub_download(
            repo_id="llmxive/videoqa-kg",
            filename="knowledge_graph.json",
            repo_type="dataset",
        )
    except Exception as exc:
        raise DataUnavailableError(
            "Failed to download knowledge graph via hf_hub_download."
        ) from exc

    # Copy the downloaded file into the project’s raw data directory.
    kg_path.write_bytes(Path(downloaded_path).read_bytes())
    logger.info(f"Knowledge graph saved to {kg_path}")
    return kg_path


# ----------------------------------------------------------------------
# 4. SHA‑256 checksum generation
# ----------------------------------------------------------------------
def _write_checksums(base_dir: Path) -> Tuple[bool, Dict[str, str]]:
    """
    Compute SHA‑256 checksums for every file under ``base_dir`` (excluding
    the manifest itself) and write ``checksums.json``.
    Returns ``(success, checksum_dict)``.
    """
    checksum_dict: Dict[str, str] = {}
    for fp in base_dir.rglob("*"):
        if fp.is_file() and fp.name != "checksums.json":
            checksum = compute_sha256(fp)
            rel_path = fp.relative_to(base_dir).as_posix()
            checksum_dict[rel_path] = checksum

    checksums_path = base_dir / "checksums.json"
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(
            [{"path": p, "sha256": h} for p, h in checksum_dict.items()],
            f,
            indent=2,
        )
    logger.info(f"Checksums written to {checksums_path}")
    return True, checksum_dict


# ----------------------------------------------------------------------
# Orchestrator
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the download of TVQA data and the knowledge graph,
    then records SHA‑256 checksums for reproducibility.
    """
    raw_dir = paths.data("raw")
    ensure_dir(raw_dir)

    try:
        _download_tvqa_train(raw_dir)
    except DataUnavailableError as exc:
        logger.error(f"Failed to download TVQA training data: {exc}")
        sys.exit(1)

    try:
        _download_tvqa_metadata(raw_dir)
    except DataUnavailableError as exc:
        logger.error(f"Failed to derive TVQA metadata: {exc}")
        sys.exit(1)

    try:
        _download_knowledge_graph(raw_dir)
    except DataUnavailableError as exc:
        logger.error(f"Failed to download knowledge graph: {exc}")
        sys.exit(1)

    # Generate checksums for everything we just wrote
    try:
        _write_checksums(raw_dir)
    except Exception as exc:  # pragma: no cover – unexpected I/O errors
        logger.error(f"Failed to write checksums: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except DataUnavailableError as exc:
        logger.error(exc)
        sys.exit(1)