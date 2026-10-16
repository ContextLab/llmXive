"""
Real-data ingestion script for the Visual Salience project.

This script verifies the presence of the OpenNeuro Moral Foundations Eye‑Tracking
Dataset (ds003123) in the expected raw data directory, attempts to download it
if missing (using the Hugging Face `datasets` library), computes SHA‑256 checksums
for all files, and writes a manifest to ``data/raw/checksums.json``. If the dataset
cannot be fetched, the script aborts with a clear ``RuntimeError`` (fail‑loud
semantics). No synthetic data fallback is performed.
"""
import json
import hashlib
import logging
import shutil
from datetime import datetime
from pathlib import Path

from llmxive_toolkit import paths, get_logger

# Import the lightweight artifact registration helper.
try:
    from utils.versioning import register_artifact
except Exception:  # pragma: no cover
    # Fallback: a no‑op if the helper is unavailable.
    def register_artifact(*_, **__):  # type: ignore
        pass

# Attempt to import the Hugging Face datasets library.
try:
    from datasets import load_dataset_builder
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "HuggingFace `datasets` library is required for automatic download."
    ) from e

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(raw_dir: Path, dataset_id: str) -> None:
    """
    Download the OpenNeuro dataset using the Hugging Face `datasets` library.
    The dataset is first prepared in its cache directory and then copied into
    ``raw_dir`` preserving the internal folder hierarchy.

    Args:
        raw_dir: Destination directory where the dataset should appear.
        dataset_id: Identifier of the OpenNeuro dataset (e.g., ``ds003123``).
    """
    logger.info(f"Dataset '{dataset_id}' not found locally – attempting automatic download.")
    repo_id = f"openneuro/{dataset_id}"
    try:
        builder = load_dataset_builder(repo_id)
        logger.info("Preparing dataset (this may take several minutes)...")
        builder.download_and_prepare()
    except Exception as e:
        logger.error(f"Failed to download dataset via Hugging Face hub: {e}")
        raise RuntimeError("DATA_DOWNLOAD_FAILED") from e

    cache_dir = Path(builder.cache_dir)
    if not cache_dir.is_dir():
        raise RuntimeError(f"Cache directory not found after download: {cache_dir}")

    logger.info(f"Copying dataset files from cache '{cache_dir}' to raw directory '{raw_dir}'.")
    shutil.copytree(cache_dir, raw_dir, dirs_exist_ok=True)

def main() -> None:
    """
    Main ingestion pipeline.

    Steps:
    1. Verify (or download) the expected raw data directory.
    2. Compute SHA‑256 checksums for every file under the raw directory.
    3. Write a manifest (including timestamps and file sizes) to ``checksums.json``.
    4. Register the manifest as an artifact.
    """
    # Use the llmxive toolkit helpers to locate the raw data root.
    raw_root = paths.data("raw")            # <project>/data/raw/
    dataset_id = "ds003123"
    raw_dir = raw_root / dataset_id          # <project>/data/raw/ds003123/
    checksum_file = raw_root / "checksums.json"

    logger.info(f"Starting ingestion verification for OpenNeuro dataset: {dataset_id}")

    # ----------------------------------------------------------------------
    # Step 1 – Verify dataset presence; download if missing.
    # ----------------------------------------------------------------------
    if not raw_dir.exists() or not any(p.is_file() for p in raw_dir.rglob("*")):
        try:
            download_dataset(raw_dir, dataset_id)
        except RuntimeError as e:
            logger.error(
                f"Dataset directory '{raw_dir}' is missing and automatic download failed. "
                "Abort with DATA_MISSING_001."
            )
            raise RuntimeError(
                "DATA_MISSING_001: Dataset not found and download failed."
            ) from e
    else:
        logger.info(f"Dataset directory already present: {raw_dir}")

    # ----------------------------------------------------------------------
    # Step 2 – Compute checksums
    # ----------------------------------------------------------------------
    logger.info("Computing SHA‑256 checksums for all files in the raw directory...")
    manifest = {
        "dataset_id": dataset_id,
        "timestamp": datetime.utcnow().isoformat(),
        "files": []
    }

    for file_path in raw_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(raw_root)
            sha256 = compute_sha256(file_path)
            manifest["files"].append({
                "path": str(rel_path),
                "sha256": sha256,
                "size": file_path.stat().st_size
            })

    # ----------------------------------------------------------------------
    # Step 3 – Write manifest
    # ----------------------------------------------------------------------
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with checksum_file.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Checksum manifest written to {checksum_file}")

    # ----------------------------------------------------------------------
    # Step 4 – Register artifact
    # ----------------------------------------------------------------------
    register_artifact(
        file_path=checksum_file,
        artifact_type="checksum_manifest",
        description="SHA‑256 manifest for OpenNeuro ds003123"
    )

    logger.info("Ingestion verification completed successfully.")

if __name__ == "__main__":
    main()
