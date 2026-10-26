"""
Data loader module for the DragMesh‑2 dataset.

This module fetches the DragMesh‑2 manifest from the HuggingFace Hub
using the lightweight ``huggingface_hub`` library (avoiding the heavy
``datasets`` dependency which requires ``pyarrow``).  The loader follows
the *fail‑loud* principle: any network, authentication, or file‑not‑found
problem raises an exception and halts the pipeline.
"""

import logging
from pathlib import Path
from typing import Optional

# Standard library imports
import os
import shutil

# Third‑party import – must be present; otherwise we raise a clear error.
try:
    # ``hf_hub_download`` is always available.
    from huggingface_hub import hf_hub_download
    # The specific exception classes may not be exported at the top level
    # in all versions of ``huggingface_hub``.  We attempt to import them,
    # falling back to generic ``Exception`` if unavailable.
    try:
        from huggingface_hub import RepositoryNotFoundError, HfHubHTTPError
    except Exception:  # pragma: no cover
        RepositoryNotFoundError = Exception  # type: ignore
        HfHubHTTPError = Exception  # type: ignore
except ImportError as exc:
    raise ImportError(
        "The 'huggingface_hub' library is required to fetch DragMesh‑2. "
        "Install it via: pip install huggingface_hub"
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

# Verified HuggingFace dataset identifier
HUGGINGFACE_DATASET_ID = "dragmesh/dragmesh-2"

# Name of the manifest file inside the repository (as stored by the dataset)
MANIFEST_FILENAME = "dragmesh_manifest.jsonl"


def ensure_dirs() -> None:
    """
    Ensure that the ``data/raw`` directory exists.
    """
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {DATA_RAW_DIR}")


def fetch_dragmesh_manifest(output_dir: Optional[Path] = None) -> Path:
    """
    Download the raw manifest file from the HuggingFace Hub.

    The function downloads **exactly one file** – the JSON‑Lines manifest –
    and returns the path to the downloaded file.  If the repository or file
    cannot be located, a clear exception is raised.

    Args:
        output_dir: Optional directory to place the downloaded file.
                    Defaults to ``data/raw``.

    Returns:
        Path to the downloaded manifest file.

    Raises:
        FileNotFoundError: If the manifest file does not exist in the repo.
        ConnectionError:   For network‑related failures.
        Exception:        For any other unexpected error.
    """
    if output_dir is None:
        output_dir = DATA_RAW_DIR

    ensure_dirs()
    logger.info(f"Fetching DragMesh‑2 manifest from {HUGGINGFACE_DATASET_ID}")

    try:
        # ``hf_hub_download`` will raise RepositoryNotFoundError or
        # HfHubHTTPError for missing repo / file / network problems.
        downloaded_path: str = hf_hub_download(
            repo_id=HUGGINGFACE_DATASET_ID,
            filename=MANIFEST_FILENAME,
            repo_type="dataset",
            # Force a fresh download each run to guarantee up‑to‑date data.
            force_download=True,
        )
        source_path = Path(downloaded_path)
        target_path = output_dir / MANIFEST_FILENAME
        # Copy to the canonical location expected by downstream code.
        shutil.copy2(source_path, target_path)
        logger.info(f"Manifest downloaded to {target_path}")
        return target_path
    except RepositoryNotFoundError as e:
        logger.error(f"Repository not found: {HUGGINGFACE_DATASET_ID}")
        raise FileNotFoundError(
            f"Repository not found: {HUGGINGFACE_DATASET_ID}"
        ) from e
    except HfHubHTTPError as e:
        logger.error(f"HTTP error while downloading manifest: {e}")
        raise ConnectionError(
            f"Failed to download manifest from HuggingFace Hub: {e}"
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error while fetching manifest: {e}")
        raise


def load_dragmesh_manifest(output_path: Optional[Path] = None) -> Path:
    """
    Public entry point used by the quick‑start script.

    It ensures the manifest is present locally (downloading it if necessary)
    and returns the path to the JSON‑Lines file.  The function **never**
    creates synthetic data; any problem results in an exception.

    Args:
        output_path: Desired location for the manifest.
                     If ``None`` the default is ``data/raw/dragmesh_manifest.jsonl``.

    Returns:
        Path to the manifest file.

    Raises:
        ConnectionError, FileNotFoundError, or generic ``Exception`` on failure.
    """
    if output_path is None:
        output_path = DEFAULT_MANIFEST_PATH

    # If the file already exists and is non‑empty, we trust it.
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"Existing manifest found at {output_path}")
        return output_path

    # Otherwise, download it.
    logger.info("Manifest not found locally – downloading from HuggingFace.")
    return fetch_dragmesh_manifest(output_dir=output_path.parent)


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

    except (ConnectionError, FileNotFoundError) as e:
        logger.critical(f"CRITICAL: Data fetch failed: {e}")
        # Re‑raise to enforce fail‑loud semantics for the pipeline.
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during fetch: {e}")
        raise


if __name__ == "__main__":
    main()
