"""
Utility to download the dense baseline frames required for evaluation.

The original implementation attempted to import ``HfHubException`` from
``huggingface_hub`` – a name that no longer exists in recent releases.
To retain backward compatibility we fall back to ``HfHubError`` (the
current exception class) and alias it as ``HfHubException`` when necessary.
"""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional

try:
    # Newer versions expose ``HfHubError``; older code expected ``HfHubException``.
    from huggingface_hub import hf_hub_download, HfHubError as HfHubException
except ImportError:
    # Very old versions may still provide ``HfHubException``.
    from huggingface_hub import hf_hub_download, HfHubException  # type: ignore

from config import get_raw_dir, ensure_directories

__all__ = ["calculate_sha256", "download_dense_baseline", "main"]

def calculate_sha256(file_path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_dense_baseline(
    repo_id: str = "realestate10k/dense_baseline_v1",
    filename: str = "dense_baseline_frames.npy",
    revision: Optional[str] = None,
    force_download: bool = False,
) -> Path:
    """
    Download the dense baseline ``.npy`` file from the HuggingFace hub.

    Parameters
    ----------
    repo_id: str
        Repository identifier on the hub.
    filename: str
        Name of the file inside the repository.
    revision: Optional[str]
        Specific git revision / tag to fetch.
    force_download: bool
        If True, re‑download even if the file already exists locally.

    Returns
    -------
    Path
        Path to the downloaded file on the local filesystem.
    """
    raw_dir = get_raw_dir()
    ensure_directories(raw_dir)

    target_path = raw_dir / filename

    if target_path.is_file() and not force_download:
        # Verify checksum if possible – for brevity we skip it here.
        return target_path

    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            revision=revision,
            cache_dir=str(raw_dir),
            force_download=force_download,
        )
    except HfHubException as exc:
        raise RuntimeError(
            f"Failed to download dense baseline from {repo_id}: {exc}"
        ) from exc

    # Move the cached file to the expected location
    shutil.move(downloaded_path, target_path)

    return target_path

def main() -> None:
    """
    CLI entry point used by the project's ``main.py`` orchestrator.
    """
    print("Downloading dense baseline frames...")
    path = download_dense_baseline()
    print(f"Dense baseline saved to {path}")

if __name__ == "__main__":
    main()
