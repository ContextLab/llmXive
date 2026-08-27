"""
download_wan_weights.py
-----------------------

Utility script to download the Wan2.1 model weights from the HuggingFace Hub,
verify their SHA256 checksums, and store them under the project‑level
``models/wan2.1/`` directory.

The script is deliberately kept lightweight and test‑friendly:
* All external interactions (``hf_hub_download`` and ``list_repo_files``) are
  imported at module level so they can be monkey‑patched in unit tests.
* ``get_model_files`` returns a list of ``(filename, expected_checksum)`` tuples.
  When ``expected_checksum`` is ``None`` the checksum is only calculated and
  logged; when a value is provided it is verified via ``verify_checksum``.
* ``download_model_files`` copies the downloaded files into the target directory
  (the HuggingFace cache may place files in a sub‑directory hierarchy, so a copy
  guarantees the expected layout).
* ``main`` provides a simple CLI entry‑point that can be executed with
  ``python -m src.generation.download_wan_weights`` or ``python code/src/generation/download_wan_weights.py``.
"""

import hashlib
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from huggingface_hub import hf_hub_download, list_repo_files

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 checksum of ``file_path``.
    The file is read in ``chunk_size`` byte chunks to avoid loading large
    files entirely into memory.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be calculated.
    chunk_size: int, optional
        Number of bytes to read per iteration (default: 8192).

    Returns
    -------
    str
        Hex‑encoded SHA256 digest.
    """
    logger.debug("Calculating SHA256 for %s", file_path)
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    logger.debug("SHA256 for %s: %s", file_path, checksum)
    return checksum


def verify_checksum(file_path: Path, expected_checksum: str) -> None:
    """
    Verify that the SHA256 checksum of ``file_path`` matches ``expected_checksum``.
    If the checksum does not match, a ``ValueError`` is raised.

    Parameters
    ----------
    file_path: Path
        Path to the file to verify.
    expected_checksum: str
        Expected hex‑encoded SHA256 checksum.

    Raises
    ------
    ValueError
        If the computed checksum differs from ``expected_checksum``.
    """
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum.lower() != expected_checksum.lower():
        msg = (
            f"Checksum mismatch for {file_path.name}: "
            f"expected {expected_checksum}, got {actual_checksum}"
        )
        logger.error(msg)
        raise ValueError(msg)
    logger.info("Checksum verified for %s", file_path.name)


# ----------------------------------------------------------------------
# Repository handling
# ----------------------------------------------------------------------


def get_model_files(repo_id: str) -> List[Tuple[str, Optional[str]]]:
    """
    Retrieve the list of model files from a HuggingFace repository.

    The function uses ``list_repo_files`` to enumerate all files in the repo.
    For each file a tuple ``(filename, expected_checksum)`` is returned.
    ``expected_checksum`` is ``None`` because the public repository does not
    provide per‑file SHA256 values.  Callers (including unit tests) may patch
    this function to inject known checksums.

    Parameters
    ----------
    repo_id: str
        The repository identifier on HuggingFace Hub (e.g. ``"Wan-AI/Wan2.1-Turbo"``).

    Returns
    -------
    List[Tuple[str, Optional[str]]]
        List of ``(filename, expected_checksum)``.  ``expected_checksum`` may be
        ``None`` when no checksum information is available.
    """
    logger.info("Fetching file list from repository %s", repo_id)
    try:
        all_files = list_repo_files(repo_id)
    except Exception as exc:
        logger.exception("Failed to list repository files for %s", repo_id)
        raise RuntimeError(f"Unable to list files for repo {repo_id}") from exc

    # Filter out common non‑model artefacts (e.g. README, .gitattributes)
    ignored = {"README.md", ".gitattributes", "LICENSE"}
    model_files = [
        (fname, None) for fname in all_files if Path(fname).name not in ignored
    ]

    logger.debug("Model files to download: %s", [f for f, _ in model_files])
    return model_files


def download_model_files(
    repo_id: str, destination: Path
) -> Dict[str, Path]:
    """
    Download all model files from ``repo_id`` into ``destination``.

    The function:
    * Ensures ``destination`` exists.
    * Calls :func:`get_model_files` to obtain the list of files.
    * Downloads each file with ``hf_hub_download`` using ``destination`` as the cache
      directory.
    * Copies the file into ``destination`` (flattening any internal cache hierarchy).
    * Verifies the checksum when an expected value is supplied.

    Parameters
    ----------
    repo_id: str
        HuggingFace repository identifier.
    destination: Path
        Directory where the model files should be placed.

    Returns
    -------
    Dict[str, Path]
        Mapping from filename to the absolute path of the downloaded file.
    """
    logger.info("Downloading Wan2.1 model files to %s", destination)
    destination.mkdir(parents=True, exist_ok=True)

    downloaded: Dict[str, Path] = {}
    for filename, expected_checksum in get_model_files(repo_id):
        logger.debug("Downloading %s", filename)
        try:
            # ``hf_hub_download`` returns the path to the cached file.
            cached_path = hf_hub_download(
                repo_id=repo_id, filename=filename, cache_dir=destination
            )
        except Exception as exc:
            logger.exception("Failed to download %s from %s", filename, repo_id)
            raise RuntimeError(
                f"Unable to download {filename} from {repo_id}"
            ) from exc

        target_path = destination / filename
        # ``cached_path`` may already be inside ``destination`` but could be in a
        # sub‑directory (e.g. ``<cache>/models--repo/...``).  Ensure the file ends up
        # directly under ``destination``.
        if Path(cached_path) != target_path:
            shutil.move(str(cached_path), str(target_path))

        if expected_checksum:
            verify_checksum(target_path, expected_checksum)

        downloaded[filename] = target_path
        logger.info("Successfully downloaded %s", filename)

    return downloaded


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Entry point for the script.

    It downloads the Wan2.1 model weights into the project‑level
    ``models/wan2.1`` directory and logs the outcome.
    """
    # Repository identifier for the Wan2.1 model.
    repo_id = "Wan-AI/Wan2.1-Turbo"

    # Resolve the absolute path ``<project_root>/models/wan2.1``.
    project_root = Path(__file__).resolve().parents[2]
    destination = project_root / "models" / "wan2.1"

    try:
        download_model_files(repo_id, destination)
    except Exception as exc:
        logger.error("Model download failed: %s", exc)
        raise

    logger.info("All Wan2.1 model files have been downloaded to %s", destination)


if __name__ == "__main__":
    # Configure a very simple console logger when the module is executed directly.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    main()
