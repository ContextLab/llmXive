"""
Real‑data ingestion script for the Visual Salience project.

This script downloads the OpenNeuro dataset (default ds003123) using
``huggingface_hub.snapshot_download`` (no ``datasets`` import to avoid
the ``pyarrow`` dependency). It validates image files, creates a SHA‑256
manifest, copies valid images to a cache directory, and writes a summary
JSON artifact. All failures raise explicit ``RuntimeError`` with the
``DATA_MISSING_001`` code so the pipeline halts loudly if data cannot be
obtained.
"""
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from huggingface_hub import snapshot_download

from config import get_paths, get_hyperparams
from utils.logging import get_logger, log_error_context
from utils.versioning import register_artifact

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def fetch_dataset(
    dataset_id: str,
    local_dir: Path,
    revision: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Download a dataset from the Hugging Face Hub using ``snapshot_download``.

    Parameters
    ----------
    dataset_id: str
        Identifier of the dataset (e.g. ``openneuro/ds003123``).
    local_dir: Path
        Directory where the dataset will be cached.
    revision: Optional[str]
        Specific tag or commit to fetch.

    Returns
    -------
    dict
        Metadata about the download.

    Raises
    ------
    RuntimeError
        If the download fails.
    """
    logger.info(f"Fetching dataset '{dataset_id}' to '{local_dir}'")
    try:
        downloaded_path = snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            local_dir=str(local_dir),
            revision=revision,
            allow_patterns=[
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.nii",
                "*.json",
                "*.tsv",
                "*.txt",
            ],
            max_workers=4,
        )
        logger.info(f"Dataset downloaded successfully to: {downloaded_path}")
        return {
            "dataset_id": dataset_id,
            "local_path": str(downloaded_path),
            "revision": revision,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Failed to download dataset '{dataset_id}': {e}")
        raise RuntimeError(
            "DATA_MISSING_001: Real data fetch failed"
        ) from e


def validate_and_cache_images(
    source_dir: Path,
    cache_dir: Path,
    checksum_manifest_path: Path,
) -> List[Dict[str, Any]]:
    """
    Validate image files in ``source_dir`` and copy the valid ones to
    ``cache_dir``.  A manifest containing SHA‑256 checksums is written to
    ``checksum_manifest_path``.

    Returns
    -------
    list[dict]
        Validation results for each image.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest if present
    expected_checksums: Dict[str, str] = {}
    if checksum_manifest_path.exists():
        logger.info(f"Loading existing checksum manifest from {checksum_manifest_path}")
        with open(checksum_manifest_path, "r") as f:
            manifest_data = json.load(f)
            for item in manifest_data.get("files", []):
                expected_checksums[item["filename"]] = item["sha256"]
    else:
        logger.info("No existing checksum manifest found – generating a new one.")

    # Gather image files
    image_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}
    image_files = [
        p for ext in image_extensions for p in source_dir.rglob(f"*{ext}")
    ] + [
        p for ext in image_extensions for p in source_dir.rglob(f"*{ext.upper()}")
    ]

    if not image_files:
        logger.warning(f"No image files found in {source_dir}")
        return []

    logger.info(f"Found {len(image_files)} image files to validate")
    validation_results = []
    new_files = []

    for img_path in image_files:
        filename = img_path.name
        try:
            actual_checksum = compute_sha256(img_path)

            if filename in expected_checksums:
                is_valid = actual_checksum == expected_checksums[filename]
                status = "valid" if is_valid else "checksum_mismatch"
            else:
                is_valid = True
                status = "new"
                new_files.append(
                    {"filename": filename, "sha256": actual_checksum}
                )

            if is_valid:
                dest_path = cache_dir / filename
                if dest_path.exists():
                    # Avoid collisions – add a short hash suffix
                    stem, suffix = filename.rsplit(".", 1)
                    dest_path = cache_dir / f"{stem}_{actual_checksum[:8]}.{suffix}"
                dest_path.write_bytes(img_path.read_bytes())
                logger.debug(f"Cached valid image: {dest_path}")
            else:
                logger.warning(
                    f"Checksum mismatch for {filename}: expected "
                    f"{expected_checksums.get(filename)}, got {actual_checksum}"
                )

            validation_results.append(
                {
                    "filename": filename,
                    "source_path": str(img_path),
                    "cache_path": str(dest_path) if is_valid else None,
                    "sha256": actual_checksum,
                    "status": status,
                    "size_bytes": img_path.stat().st_size,
                }
            )
        except Exception as e:
            logger.error(f"Error processing {img_path}: {e}")
            validation_results.append(
                {
                    "filename": filename,
                    "source_path": str(img_path),
                    "cache_path": None,
                    "sha256": None,
                    "status": "error",
                    "error": str(e),
                }
            )

    # Write/Update manifest
    manifest_content = {
        "dataset_id": source_dir.parent.name,
        "generated_at": datetime.utcnow().isoformat(),
        "files": validation_results,
    }
    checksum_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_manifest_path, "w") as f:
        json.dump(manifest_content, f, indent=2)

    logger.info(
        f"Checksum manifest written to {checksum_manifest_path} "
        f"({len(validation_results)} entries)"
    )

    # Register manifest as an artifact
    register_artifact(
        checksum_manifest_path,
        artifact_type="checksum_manifest",
        description="SHA‑256 manifest for downloaded images",
    )

    return validation_results


def main() -> Dict[str, Any]:
    """
    Entry point for the ingestion pipeline.

    Returns
    -------
    dict
        Summary of the ingestion process.
    """
    paths = get_paths()
    hyperparams = get_hyperparams()

    # Default to the dataset required by the project spec
    dataset_id = hyperparams.get(
        "dataset_id", "openneuro/ds003123"
    )  # ds003123 is the target dataset
    revision = hyperparams.get("dataset_revision", None)

    # Resolve directories using the canonical Paths defined in ``config``
    raw_data_dir = paths.DATA_RAW / dataset_id.split("/")[-1]
    cache_dir = paths.DATA_PROCESSED / "images"
    manifest_path = paths.DATA_INTERIM / "dataset_checksums.json"

    # Ensure required parent directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    paths.DATA_INTERIM.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting ingestion for dataset: {dataset_id}")

    try:
        # Step 1 – download the dataset
        fetch_result = fetch_dataset(dataset_id, raw_data_dir, revision)

        if fetch_result["status"] != "success":
            raise RuntimeError(
                "DATA_MISSING_001: Real data fetch failed – non‑success status"
            )

        # Step 2 – validate images and build the checksum manifest
        validation_results = validate_and_cache_images(
            raw_data_dir, cache_dir, manifest_path
        )

        if not validation_results:
            raise RuntimeError(
                "DATA_MISSING_001: No valid image files found after download"
            )

        # Step 3 – write a concise summary artifact
        valid_cnt = sum(
            1 for r in validation_results if r["status"] in ("valid", "new")
        )
        invalid_cnt = len(validation_results) - valid_cnt

        summary = {
            "status": "success",
            "dataset_id": dataset_id,
            "total_files": len(validation_results),
            "valid_files": valid_cnt,
            "invalid_files": invalid_cnt,
            "cache_dir": str(cache_dir),
            "manifest_path": str(manifest_path),
        }

        summary_path = paths.DATA_INTERIM / "ingestion_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)

        register_artifact(
            summary_path,
            artifact_type="ingestion_summary",
            description="Summary of dataset download and validation",
        )

        logger.info(f"Ingestion summary written to {summary_path}")
        return summary

    except Exception as e:
        # Log rich context before re‑raising – the pipeline must fail loudly
        log_error_context(e, "Data ingestion failed")
        raise


if __name__ == "__main__":
    # Running as a script will exit with a non‑zero code on failure
    try:
        main()
    except RuntimeError as err:
        logger.error(str(err))
        raise