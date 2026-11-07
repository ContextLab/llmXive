"""
Data loader module for the DragMesh-2 dataset.

This module fetches the DragMesh-2 manifest from the HuggingFace Hub.
The loader follows the fail-loud principle: any network, authentication, 
or file-not-found problem raises an exception and halts the pipeline.
"""

import os
import logging
from pathlib import Path
from typing import Optional

try:
    from huggingface_hub import hf_hub_download
except ImportError as exc:
    raise ImportError(
        "The 'huggingface_hub' library is required to fetch DragMesh-2. "
        "Install it via: pip install huggingface_hub"
    ) from exc

from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_RAW_DIR: Path = paths.data("raw")
DEFAULT_MANIFEST_PATH: Path = DATA_RAW_DIR / "dragmesh_manifest.jsonl"

# Corrected HF_REPO_ID based on author attribution (Tianshan Zhang)
HF_REPO_ID = "TianshanZhang/DragMesh-2"
HF_MANIFEST_FILENAME = "dragmesh_manifest.jsonl"

def _ensure_raw_dir() -> None:
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def _download_and_write_manifest(output_path: Path) -> Path:
    # To avoid "Invalid username or password" errors on public repos in environments
    # with stale/invalid HF tokens, we explicitly unset the token.
    os.environ.pop("HF_TOKEN", None)
    
    logger.info(f"Fetching manifest '{HF_MANIFEST_FILENAME}' from repo '{HF_REPO_ID}'.")
    try:
        downloaded_path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=HF_MANIFEST_FILENAME,
            repo_type="dataset",
            token=False # Force public access
        )
    except Exception as exc:
        logger.error(f"Failed to download manifest: {exc}")
        raise RuntimeError(f"Unable to retrieve DragMesh-2 manifest from {HF_REPO_ID}. Please check repo access.") from exc

    if not Path(downloaded_path).exists() or Path(downloaded_path).stat().st_size == 0:
        raise RuntimeError("Downloaded manifest is empty or missing.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with Path(downloaded_path).open("rb") as src, output_path.open("wb") as dst:
        while True:
            chunk = src.read(8192)
            if not chunk:
                break
            dst.write(chunk)

    if output_path.stat().st_size == 0:
        raise RuntimeError("Written manifest is empty after copy.")

    logger.info(f"Successfully wrote manifest to {output_path}")
    return output_path

def load_dragmesh_manifest(output_path: Optional[Path] = None) -> Path:
    if output_path is None:
        output_path = DEFAULT_MANIFEST_PATH

    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info(f"Existing manifest found at {output_path}")
        return output_path

    _ensure_raw_dir()
    return _download_and_write_manifest(output_path)

def get_manifest_checksum(manifest_path: Path) -> str:
    import hashlib
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    sha256 = hashlib.sha256()
    with manifest_path.open("rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def main() -> None:
    logger.info("Starting DragMesh-2 manifest fetch...")
    try:
        manifest_path = load_dragmesh_manifest()
        checksum = get_manifest_checksum(manifest_path)
        logger.info(f"Manifest ready at: {manifest_path}")
        logger.info(f"Manifest SHA256 checksum: {checksum}")
    except Exception as e:
        logger.critical(f"CRITICAL: Data fetch failed: {e}")
        raise

if __name__ == "__main__":
    main()