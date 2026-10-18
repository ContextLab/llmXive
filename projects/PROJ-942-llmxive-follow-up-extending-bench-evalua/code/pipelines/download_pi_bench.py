import argparse
import hashlib
import logging
from pathlib import Path
from typing import List, Tuple

from huggingface_hub import HfApi, hf_hub_download
from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

# Constants for the dataset
REPO_ID = "allenai/pi_bench"
REPO_TYPE = "dataset"

def _list_repo_files() -> List[str]:
    """
    Retrieve a list of all file paths in the remote repository.
    """
    api = HfApi()
    # `repo_files` returns a list of file paths relative to the repo root.
    repo_files = api.list_repo_files(repo_id=REPO_ID, repo_type=REPO_TYPE)
    # Filter out any hidden files that are not part of the dataset payload
    # (e.g., .gitattributes, .gitignore, README, etc.)
    data_files = [f for f in repo_files if not f.startswith(".")]
    log.debug(f"Found {len(data_files)} files in the repository.")
    return data_files

def _download_file(filename: str, target_dir: Path) -> Path:
    """
    Download a single file from the hub into ``target_dir`` preserving its relative path.
    Returns the local Path of the downloaded file.
    """
    local_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        repo_type=REPO_TYPE,
        local_dir=target_dir,
    )
    log.debug(f"Downloaded {filename} → {local_path}")
    return Path(local_path)

def _sha256_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_checksums(files: List[Tuple[Path, str]], out_path: Path) -> None:
    """
    Write a manifest of SHA‑256 checksums.
    ``files`` is a list of (relative_path, checksum) tuples.
    """
    with out_path.open("w", encoding="utf-8") as f:
        for rel_path, checksum in files:
            f.write(f"{checksum}  {rel_path}\n")
    log.info(f"Checksum manifest written to {out_path}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the π‑Bench dataset into data/raw using huggingface_hub."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files (used for downstream pipelines)",
    )
    args = parser.parse_args()
    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Starting download of repository '{REPO_ID}' (type={REPO_TYPE})")
    try:
        file_list = _list_repo_files()
    except Exception as exc:
        log.error(f"Failed to list files in repository {REPO_ID}: {exc}")
        raise

    checksums: List[Tuple[Path, str]] = []
    for repo_file in file_list:
        try:
            local_path = _download_file(repo_file, raw_dir)
            # Compute checksum relative to the raw_dir root
            rel_path = local_path.relative_to(raw_dir)
            checksum = _sha256_checksum(local_path)
            checksums.append((rel_path, checksum))
        except Exception as exc:
            log.error(f"Error downloading or processing file '{repo_file}': {exc}")
            raise

    # Write a simple manifest file listing the downloaded files
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        for repo_file in file_list:
            mf.write(f"{repo_file}\n")
    log.info(f"Download manifest written to {manifest_path}")

    # Write checksum file
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("π‑Bench dataset download completed successfully.")

if __name__ == "__main__":
    main()
