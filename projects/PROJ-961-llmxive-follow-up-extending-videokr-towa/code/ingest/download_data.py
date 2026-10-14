"""
Data download module for fetching VideoKR‑SFT and Knowledge Graph.
This script attempts to download the required files from the official
Hugging Face Hub repository defined in ``utils.config.VIDEO_KR_REPO``.
If that fails, it falls back to the public GitHub raw URLs.
If both attempts fail, a ``DataUnavailableError`` is raised – no synthetic
fallback is performed.
After successful download, SHA‑256 checksums for each file are recorded
in ``data/raw/checksums.json``.
"""
import logging
import json
import sys
from pathlib import Path
from typing import List, Dict

# Ensure the code/ directory is in the python path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from huggingface_hub import hf_hub_download
from datasets import load_dataset  # noqa: F401

# Import project configuration utilities
from utils.config import get_path, ensure_dir, VIDEO_KR_REPO, PATHS
# Fixed import to use the correct module path relative to code/
from ingest.checksum import compute_sha256

logger = logging.getLogger(__name__)


class DataUnavailableError(RuntimeError):
    """Raised when the required dataset or graph cannot be fetched."""


def _download_via_hf(repo_id: str, filename: str, target_dir: Path) -> Path:
    """
    Attempt to download a single file from the Hugging Face Hub.
    """
    try:
        logger.info(f"Attempting to download '{filename}' from repo '{repo_id}' via HF Hub.")
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(target_dir),
            force_download=False,
            resume_download=True,
        )
        target_path = target_dir / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Move file from HF cache to the target_dir
        Path(downloaded_path).replace(target_path)
        logger.info(f"Successfully downloaded {filename} to {target_path}")
        return target_path
    except Exception as e:
        logger.warning(f"Hugging Face Hub download failed for {filename}: {e}")
        raise DataUnavailableError(
            f"Hugging Face Hub download failed for {filename}."
        ) from e


def _download_via_github_raw(url: str, target_path: Path) -> Path:
    """
    Fallback download using a raw GitHub URL.
    """
    try:
        logger.info(f"Attempting fallback download from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Fallback download succeeded: {target_path}")
        return target_path
    except Exception as e:
        logger.error(f"Fallback download failed for {url}: {e}")
        raise DataUnavailableError(
            f"Unable to download from fallback URL: {url}"
        ) from e


def _download_file(repo_id: str, filename: str, target_dir: Path) -> Path:
    """
    Download a file, trying HF Hub first and then a GitHub raw fallback.
    """
    try:
        return _download_via_hf(repo_id, filename, target_dir)
    except DataUnavailableError:
        # Construct the official VideoKR GitHub raw URL
        github_raw_url = f"https://raw.githubusercontent.com/VideoKR/VideoKR-SFT/main/{filename}"
        return _download_via_github_raw(github_raw_url, target_dir / filename)


def _write_checksums(entries: List[Dict[str, str]], output_path: Path) -> None:
    """
    Write a list of checksum entries to ``output_path`` as a JSON list.
    """
    ensure_dir(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    logger.info(f"Checksum file written to {output_path}")


def main() -> None:
    """
    Main entry point for the download module.
    """
    raw_dir: Path = PATHS["raw"]
    ensure_dir(raw_dir)

    # Expected filenames in the repository
    filenames = ["videokr_sft.json", "knowledge_graph.json"]
    downloaded_paths: List[Path] = []

    for fn in filenames:
        downloaded_paths.append(_download_file(VIDEO_KR_REPO, fn, raw_dir))

    # Compute checksums
    checksum_entries = []
    for path in downloaded_paths:
        checksum = compute_sha256(path)
        entry = {
            "path": str(path.relative_to(raw_dir).as_posix()),
            "sha256": checksum,
        }
        checksum_entries.append(entry)

    # Write combined checksum file
    checksum_file = raw_dir / "checksums.json"
    _write_checksums(checksum_entries, checksum_file)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    try:
        main()
    except DataUnavailableError as e:
        logger.error(e)
        # Propagate the error with a non-zero exit code as required
        sys.exit(1)