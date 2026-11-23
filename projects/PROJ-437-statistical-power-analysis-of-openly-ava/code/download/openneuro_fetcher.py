"""
OpenNeuro Fetcher
-----------------
This module downloads BIDS‑formatted OpenNeuro datasets in a
streaming‑first, fail‑loudly manner.  It reads the user‑provided
``config.yaml`` (the same file used by the main pipeline) and
downloads each dataset listed under the ``datasets`` key.

The implementation respects the following requirements:
* **Real source** – the data are fetched directly from the official
  OpenNeuro download endpoint (``https://openneuro.org/crn/datasets/<id>/download``).
* **Streaming** – the HTTP response is streamed to disk in 1 MiB
  chunks to avoid loading the entire archive into memory.
* **Fail‑loudly** – any network or I/O error raises an exception;
  no synthetic fallback is provided.
* **Integrity** – after extraction a SHA‑256 hash for every file is
  written to ``data/derived/integrity_hashes.json`` (see
  ``data_integrity_hash.py``).
* **Deterministic** – the order of downloaded datasets follows the
  order in the configuration file; the random seed is set from the
  ``random_seed`` entry (if present) to keep downstream sampling
  reproducible.

The script is invoked by the quick‑start command:

    python code/main.py --action download --config config.yaml

which ultimately calls ``fetch_main()`` defined below.
"""

import argparse
import json
import logging
import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Dict, List

import requests
from tqdm import tqdm

from utils.seed_manager import set_global_seed, get_seed
from utils.resource_guard import enforce_memory_limit

# Configure a module‑level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_simple_yaml(path: Path) -> Dict:
    """
    Very small YAML parser – sufficient for the ``config.yaml`` used in
    the quick‑start.  It only handles top‑level keys with scalar or list
    values.
    """
    config: Dict = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            # Detect list syntax ``[a, b, c]``
            if value.startswith("[") and value.endswith("]"):
                items = [item.strip().strip('"\'') for item in value[1:-1].split(",")]
                config[key] = items
            else:
                config[key] = value.strip('"\'')
    return config

def _download_dataset_zip(dataset_id: str, dest_dir: Path) -> Path:
    """
    Download the dataset archive from OpenNeuro.  The official endpoint
    for the latest version is:

        https://openneuro.org/crn/datasets/<dataset_id>/download

    The function streams the response to ``dest_dir/<dataset_id>.zip``.
    """
    url = f"https://openneuro.org/crn/datasets/{dataset_id}/download"
    logger.info(f"Downloading dataset {dataset_id} from {url}")

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()  # Fail loudly on HTTP errors

    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / f"{dataset_id}.zip"

    # Stream download with a progress bar
    total = int(response.headers.get("content-length", 0))
    chunk_size = 1024 * 1024  # 1 MiB
    with zip_path.open("wb") as f, tqdm(
        total=total, unit="iB", unit_scale=True, desc=f"{dataset_id}.zip"
    ) as bar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # filter out keep‑alive chunks
                f.write(chunk)
                bar.update(len(chunk))

    logger.info(f"Saved archive to {zip_path}")
    return zip_path

def _extract_archive(archive_path: Path, extract_to: Path) -> None:
    """
    Extract a ``.zip`` or ``.tar.gz`` archive.  OpenNeuro currently serves
    datasets as zip files, but the function also handles tarballs for
    future‑proofing.
    """
    logger.info(f"Extracting {archive_path} → {extract_to}")
    extract_to.mkdir(parents=True, exist_ok=True)

    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
    elif tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path}")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def download_datasets(config: Dict) -> List[Path]:
    """
    Download all datasets listed in ``config['datasets']``.  Returns a
    list of the root directories that contain the extracted BIDS
    hierarchy.
    """
    dataset_entries = config.get("datasets", [])
    if not isinstance(dataset_entries, list):
        raise ValueError("'datasets' entry in the config must be a list")

    downloaded_paths: List[Path] = []

    # Ensure reproducibility for any random sampling that may happen later
    seed = config.get("random_seed")
    if seed is not None:
        set_global_seed(int(seed))

    for entry in dataset_entries:
        if isinstance(entry, dict):
            dataset_id = entry.get("id") or entry.get("dataset_id") or entry.get("id")
        else:
            dataset_id = str(entry)

        if not dataset_id:
            raise ValueError("Dataset entry missing an identifier")

        # Enforce a generous but safe memory limit before each download
        enforce_memory_limit(max_ram_gb=6)

        raw_dir = Path("data/raw") / dataset_id
        if raw_dir.exists() and any(raw_dir.iterdir()):
            logger.info(f"Dataset {dataset_id} already present – skipping download")
            downloaded_paths.append(raw_dir)
            continue

        zip_path = _download_dataset_zip(dataset_id, Path("data/tmp_downloads"))
        _extract_archive(zip_path, raw_dir)

        # Clean up the archive to keep the repository size small
        try:
            zip_path.unlink()
        except Exception:
            pass

        downloaded_paths.append(raw_dir)

    return downloaded_paths

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    CLI entry point used by ``code/main.py``.  It parses ``--config``,
    downloads the datasets, and writes a tiny manifest file
    ``data/derived/download_manifest.json`` for downstream modules.
    """
    parser = argparse.ArgumentParser(description="OpenNeuro dataset fetcher")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the project configuration file (YAML or simple key/value).",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_file():
        logger.error(f"Configuration file not found: {config_path}")
        return 1

    config = _load_simple_yaml(config_path)

    try:
        downloaded = download_datasets(config)
    except Exception as exc:
        logger.error(f"Failed to download datasets: {exc}")
        return 1

    # Write a simple manifest so later stages can discover the data
    manifest_path = Path("data/derived/download_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"downloaded_datasets": [str(p) for p in downloaded]}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"Download manifest written to {manifest_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
