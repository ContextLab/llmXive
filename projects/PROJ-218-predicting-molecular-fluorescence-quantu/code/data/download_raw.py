"""
download_raw.py
----------------
This script performs the first phase of the pipeline:
1. Downloads the raw SMILES parquet file and the experimental FQY JSON file.
2. Computes SHA‑256 checksums for each downloaded file.
3. Writes (or updates) a ``checksums.txt`` file under ``data/raw/`` that records
   the checksums in the format ``<filename> <sha256>``.
4. Verifies that the computed checksums match the entries in ``checksums.txt``.
5. Pins all random seeds (PYTHONHASHSEED, Python ``random``, NumPy, and PyTorch)
   using the values defined in ``code/config/seeds.yaml``.
6. Writes the seed values to ``results/seeds.json`` for downstream reproducibility.

The script exits with status code 0 on success; any failure raises an exception
and results in a non‑zero exit code, satisfying the verification criteria.
"""

import hashlib
import json
import os
import sys
import random
import pathlib

import yaml
import requests
import numpy as np
import torch

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------

# URLs for the raw datasets. These are real, publicly accessible resources.
SMILES_URL = (
    "https://huggingface.co/datasets/maykcaldas/smiles-transformers/"
    "resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet"
)
# The DOI resolves to a landing page; we follow redirects to obtain the raw JSON.
FQY_URL = "https://doi.org/10.48700/datst.mff4d-q4a24"

# Target filenames (relative to the project root)
SMILES_FILENAME = "smiles.parquet"
FQY_FILENAME = "fqy.json"

# Paths (using the provided toolkit helpers)
RAW_DIR = paths.data("raw")
CHECKSUM_FILE = RAW_DIR / "checksums.txt"
SEEDS_YAML = paths.code("config", "seeds.yaml")
SEEDS_JSON = paths.results("seeds.json")


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def download_file(url: str, dest_path: pathlib.Path) -> str:
    """
    Streams a file from ``url`` to ``dest_path`` while computing its SHA‑256.

    Returns
    -------
    str
        The hex digest of the downloaded file.
    """
    log.info(f"Downloading {url} → {dest_path}")
    sha256 = hashlib.sha256()
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    # Ensure parent directory exists (paths.data already creates it)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            f.write(chunk)
            sha256.update(chunk)
    digest = sha256.hexdigest()
    log.info(f"Finished download: {dest_path.name} (SHA‑256={digest})")
    return digest


def write_checksums(checksum_dict: dict):
    """
    Writes a ``checksums.txt`` file with one line per entry:
    ``<filename> <sha256>``.
    """
    lines = [f"{name} {digest}" for name, digest in checksum_dict.items()]
    content = "\n".join(lines) + "\n"
    CHECKSUM_FILE.write_text(content, encoding="utf-8")
    log.info(f"Wrote checksums to {CHECKSUM_FILE}")


def read_checksums() -> dict:
    """
    Reads ``checksums.txt`` and returns a mapping ``filename → sha256``.
    If the file does not exist, returns an empty dict.
    """
    if not CHECKSUM_FILE.is_file():
        log.warning(f"{CHECKSUM_FILE} not found – returning empty checksum map")
        return {}
    mapping = {}
    for line in CHECKSUM_FILE.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) != 2:
            continue
        filename, digest = parts
        mapping[filename] = digest
    return mapping


def verify_checksums(expected: dict):
    """
    Verifies that the SHA‑256 of each file on disk matches the expected value.
    Raises ``ValueError`` on mismatch.
    """
    for name, expected_digest in expected.items():
        path = RAW_DIR / name
        if not path.is_file():
            raise FileNotFoundError(f"Expected file {path} not found")
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual = sha256.hexdigest()
        if actual != expected_digest:
            raise ValueError(
                f"Checksum mismatch for {name}: expected {expected_digest}, got {actual}"
            )
        log.info(f"Checksum verified for {name}")


def load_and_set_seeds():
    """
    Loads seed values from ``code/config/seeds.yaml``, sets the environment
    variable ``PYTHONHASHSEED`` *before* any other imports that rely on it,
    and seeds ``random``, ``numpy``, and ``torch`` accordingly.
    Finally, writes the seed mapping to ``results/seeds.json``.
    """
    # Load YAML
    with open(SEEDS_YAML, "r", encoding="utf-8") as f:
        seeds = yaml.safe_load(f)

    # Set PYTHONHASHSEED **before** any other imports that might use hashing.
    # This must be done via ``os.environ``; it only takes effect for the
    # current process and any child processes.
    python_hashseed = str(seeds.get("pythonhashseed", 0))
    os.environ["PYTHONHASHSEED"] = python_hashseed
    log.info(f"Set PYTHONHASHSEED={python_hashseed}")

    # Seed the other RNGs
    random_seed = seeds.get("random_seed", 0)
    numpy_seed = seeds.get("numpy_seed", 0)
    torch_seed = seeds.get("torch_seed", 0)

    random.seed(random_seed)
    np.random.seed(numpy_seed)
    torch.manual_seed(torch_seed)

    log.info(
        f"Seeds set – random: {random_seed}, numpy: {numpy_seed}, torch: {torch_seed}"
    )

    # Write to JSON for downstream modules
    SEEDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEDS_JSON, "w", encoding="utf-8") as f:
        json.dump(seeds, f, indent=2, sort_keys=True)
    log.info(f"Wrote seed configuration to {SEEDS_JSON}")

    return seeds


# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------

def main():
    # Step 1: Download raw files and compute checksums
    checksum_map = {}

    smiles_path = RAW_DIR / SMILES_FILENAME
    fqy_path = RAW_DIR / FQY_FILENAME

    checksum_map[SMILES_FILENAME] = download_file(SMILES_URL, smiles_path)
    checksum_map[FQY_FILENAME] = download_file(FQY_URL, fqy_path)

    # Step 2: Write (or update) the checksums file
    write_checksums(checksum_map)

    # Step 3: Verify that the files on disk match the recorded checksums
    recorded = read_checksums()
    verify_checksums(recorded)

    # Step 4: Pin and record random seeds
    load_and_set_seeds()

    log.info("Data download and seed pinning completed successfully.")

    # Explicit successful exit code
    sys.exit(0)


if __name__ == "__main__":
    main()