import argparse
import hashlib
import logging
from pathlib import Path
from typing import List, Tuple

import requests
from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

# List of public JSON files to download as a stand‑in for the π‑Bench dataset.
# These files are fetched from openly accessible URLs and are genuine JSON data.
# The list can be extended with additional files if needed.
PUBLIC_JSON_URLS = [
    # Example JSON file from the Hugging Face datasets repository.
    # This file is small, publicly accessible, and can be loaded with `datasets.load_dataset("json", ...)`.
    "https://raw.githubusercontent.com/huggingface/datasets/main/datasets/json/example.json",
]

def _download_file(url: str, target_dir: Path) -> Path:
    """
    Download a single file from ``url`` into ``target_dir``.
    Returns the local Path of the downloaded file.
    """
    local_path = target_dir / Path(url).name
    log.debug(f"Downloading {url} → {local_path}")
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    with local_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return local_path

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
        description="Download a small public JSON dataset to act as a placeholder for π‑Bench."
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

    log.info("Starting download of public JSON files.")
    checksums: List[Tuple[Path, str]] = []

    for url in PUBLIC_JSON_URLS:
        try:
            local_path = _download_file(url, raw_dir)
            rel_path = local_path.relative_to(raw_dir)
            checksum = _sha256_checksum(local_path)
            checksums.append((rel_path, checksum))
        except Exception as exc:
            log.error(f"Failed to download or process {url}: {exc}")
            raise

    # Write a simple manifest file listing the downloaded files
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        for url in PUBLIC_JSON_URLS:
            mf.write(f"{url}\n")
    log.info(f"Download manifest written to {manifest_path}")

    # Write checksum file
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("Placeholder dataset download completed successfully.")

if __name__ == "__main__":
    main()
