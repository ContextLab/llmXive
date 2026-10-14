"""
Data download module for fetching VideoKR‑SFT and Knowledge Graph.
This script attempts to download the required files from the official
Hugging Face Hub repository defined in ``utils.config.VIDEO_KR_REPO``.
If the download fails, a ``DataUnavailableError`` is raised – no synthetic
fallback is performed.
After successful download, SHA‑256 checksums for each file are recorded
in ``data/raw/checksums.json`` using the checksum utilities.
"""
import logging
import json
from pathlib import Path
from typing import List, Dict

# Import project configuration utilities using the correct package path.
from code.utils.config import get_path, ensure_dir, VIDEO_KR_REPO, PATHS

# Checksum helper from the ingestion utilities.
from code.ingest.checksum import compute_sha256

logger = logging.getLogger(__name__)


class DataUnavailableError(RuntimeError):
    """Raised when the required dataset or graph cannot be fetched."""


def _download_file(repo_id: str, filename: str, target_dir: Path) -> Path:
    """
    Helper that downloads a single file from the Hugging Face Hub.

    Args:
        repo_id (str): Repository identifier on the Hub.
        filename (str): Name of the file inside the repo.
        target_dir (Path): Directory where the file should be placed.

    Returns:
        Path: Path to the downloaded file.

    Raises:
        DataUnavailableError: If the download fails for any reason.
    """
    try:
        # Import inside the function so that a missing ``huggingface_hub``
        # package raises a controlled error rather than breaking module import.
        from huggingface_hub import hf_hub_download
    except Exception as import_err:
        logger.error(
            "huggingface_hub package is required but not installed. "
            "Install it via the project's requirements.txt."
        )
        raise DataUnavailableError(
            "huggingface_hub is not available; cannot download files."
        ) from import_err

    try:
        logger.info(f"Attempting to download '{filename}' from repo '{repo_id}'.")
        # Explicitly specify that we are downloading a dataset repository.
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            repo_type="dataset",
            cache_dir=str(target_dir),
            force_download=False,
            resume_download=True,
        )
        # Ensure the file ends up exactly where we expect.
        target_path = target_dir / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)
        # ``hf_hub_download`` may return a cached location; move it to the target.
        Path(downloaded_path).replace(target_path)
        logger.info(f"Successfully downloaded to {target_path}")
        return target_path
    except Exception as e:  # Broad catch to handle version differences in HF errors.
        logger.error(f"Failed to download {filename} from {repo_id}: {e}")
        raise DataUnavailableError(
            f"Unable to fetch required file '{filename}' from repository '{repo_id}'."
        ) from e


def _write_checksums(entries: List[Dict[str, str]], output_path: Path) -> None:
    """
    Write a list of checksum entries to ``output_path`` as a JSON list.

    Args:
        entries (List[Dict[str, str]]): List of ``{\"path\": ..., \"sha256\": ...}`` dicts.
        output_path (Path): Destination file.
    """
    ensure_dir(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
    logger.info(f"Checksum file written to {output_path}")


def main() -> None:
    """
    Main entry point for the download module.

    - Downloads ``videokr_sft.json`` and ``knowledge_graph.json`` from the
      Hugging Face Hub repository defined in ``utils.config.VIDEO_KR_REPO``.
    - Computes SHA‑256 checksums for each file.
    - Writes a combined checksum list to ``data/raw/checksums.json``.
    - Exits with a non‑zero status code if any download fails.
    """
    raw_dir: Path = PATHS["raw"]
    ensure_dir(raw_dir)

    # Expected filenames in the repository.
    filenames = ["videokr_sft.json", "knowledge_graph.json"]
    downloaded_paths: List[Path] = []

    for fn in filenames:
        downloaded_paths.append(_download_file(VIDEO_KR_REPO, fn, raw_dir))

    # Compute checksums.
    checksum_entries = []
    for path in downloaded_paths:
        checksum = compute_sha256(path)
        entry = {
            "path": str(path.relative_to(raw_dir).as_posix()),
            "sha256": checksum,
        }
        checksum_entries.append(entry)

    # Write combined checksum file.
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
        # Propagate the error with a non‑zero exit code as required.
        raise SystemExit(1)
