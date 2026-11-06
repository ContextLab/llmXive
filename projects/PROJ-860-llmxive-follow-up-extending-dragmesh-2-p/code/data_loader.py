"""
Data loader module for the DragMesh‑2 dataset.

This module fetches the DragMesh‑2 manifest from the HuggingFace Hub
using the `datasets` library (which handles repository layout
automatically).  The loader follows the *fail‑loud* principle: any
network, authentication, or file‑not‑found problem raises an exception
and halts the pipeline.
"""

import logging
from pathlib import Path
from typing import Optional

# Third‑party imports – must be present; otherwise we raise a clear error.
try:
    from datasets import load_dataset
except ImportError as exc:
    raise ImportError(
        "The 'datasets' library is required to fetch DragMesh‑2. "
        "Install it via: pip install datasets"
    ) from exc

# Configure module‑level logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Project‑relative paths (created via llmxive_toolkit.paths in runtime)
from llmxive_toolkit import paths

# Default locations
DATA_RAW_DIR: Path = paths.data("raw")
DEFAULT_MANIFEST_PATH: Path = DATA_RAW_DIR / "dragmesh_manifest.jsonl"

# HuggingFace dataset identifier (official DragMesh‑2 repository)
HF_DATASET_ID = "dragmesh/dragmesh-2"

def _ensure_raw_dir() -> None:
    """Ensure that the ``data/raw`` directory exists."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {DATA_RAW_DIR}")

def _download_and_write_manifest(
    output_path: Path,
) -> Path:
    """
    Download the DragMesh‑2 dataset using ``datasets.load_dataset`` and
    write a line‑delimited JSON manifest to ``output_path``.

    The function streams the dataset to avoid loading the entire
    collection into memory (the dataset is modest in size, but streaming
    is a safe default).

    Args:
        output_path: Destination path for the JSON‑Lines manifest.

    Returns:
        Path to the written manifest file.

    Raises:
        RuntimeError: If the dataset cannot be accessed or the written
                      file is empty.
    """
    logger.info(f"Fetching DragMesh‑2 dataset '{HF_DATASET_ID}' via `datasets`.")
    # Load the dataset in streaming mode; this works for most HF datasets.
    try:
        ds = load_dataset(
            HF_DATASET_ID,
            split="train",
            streaming=True,
        )
    except Exception as exc:
        logger.error(f"Failed to load dataset {HF_DATASET_ID}: {exc}")
        raise

    # Write each example as a JSON line.
    with output_path.open("w", encoding="utf-8") as f:
        count = 0
        for example in ds:
            # ``datasets`` returns dict‑like objects; we convert to plain dict.
            f.write(f"{example}\n")
            count += 1
            # Safety guard: stop after an unreasonable number of rows.
            if count > 10_000_000:
                logger.error(
                    "Dataset appears unexpectedly large; aborting after "
                    f"{count} rows to protect resources."
                )
                raise RuntimeError("Dataset too large to write safely.")
    if count == 0:
        raise RuntimeError("Downloaded dataset is empty; no manifest generated.")
    logger.info(f"Successfully wrote {count} rows to manifest at {output_path}")
    return output_path

def load_dragmesh_manifest(
    output_path: Optional[Path] = None,
) -> Path:
    """
    Public entry point used by the quick‑start script.

    Ensures the manifest is present locally (downloading it if necessary)
    and returns the path to the JSON‑Lines file.  The function **never**
    creates synthetic data; any problem results in an exception.

    Args:
        output_path: Desired location for the manifest.
                     If ``None`` the default is
                     ``data/raw/dragmesh_manifest.jsonl``.

    Returns:
        Path to the manifest file.

    Raises:
        ConnectionError, FileNotFoundError, RuntimeError, or generic
        ``Exception`` on failure.
    """
    if output_path is None:
        output_path = DEFAULT_MANIFEST_PATH

    # If the file already exists and is non‑empty, we trust it.
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"Existing manifest found at {output_path}")
        return output_path

    # Otherwise, download it.
    _ensure_raw_dir()
    logger.info("Manifest not found locally – downloading from HuggingFace.")
    return _download_and_write_manifest(output_path)

def get_manifest_checksum(manifest_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of the manifest file.

    Args:
        manifest_path: Path to the JSON‑Lines manifest.

    Returns:
        Hexadecimal SHA‑256 digest.

    Raises:
        FileNotFoundError: If the manifest does not exist.
    """
    import hashlib

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    sha256 = hashlib.sha256()
    with manifest_path.open("rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def main() -> None:
    """
    Entry point invoked via ``python -m code.data_loader`` or directly
    ``python code/data_loader.py``.  It downloads the manifest (if needed),
    validates that it is non‑empty, and logs its SHA‑256 checksum.
    """
    logger.info("Starting DragMesh‑2 manifest fetch...")
    try:
        manifest_path = load_dragmesh_manifest()
        logger.info(f"Manifest ready at: {manifest_path}")

        if not manifest_path.exists() or manifest_path.stat().st_size == 0:
            raise FileNotFoundError(
                "Generated manifest is empty or missing."
            )

        checksum = get_manifest_checksum(manifest_path)
        logger.info(f"Manifest SHA256 checksum: {checksum}")

    except (ConnectionError, FileNotFoundError, RuntimeError) as e:
        logger.critical(f"CRITICAL: Data fetch failed: {e}")
        # Re‑raise to enforce fail‑loud semantics for the pipeline.
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during fetch: {e}")
        raise

if __name__ == "__main__":
    main()
