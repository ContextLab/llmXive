"""
Download raw datasets (GSM8K, MATH, MMLU‑STEM) and store them as Parquet files.
Generates a SHA‑256 manifest at `state/artifact_hashes.yaml`.
"""

import sys
import hashlib
from pathlib import Path

import yaml
from datasets import load_dataset
import pandas as pd

# Project configuration utilities
from src.utils.config import get_config

def ensure_directories() -> None:
    """
    Ensure that the raw data and state directories exist.
    """
    cfg = get_config()
    cfg.data_raw.mkdir(parents=True, exist_ok=True)
    cfg.state_dir.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_manifest(manifest_path: Path) -> dict:
    """
    Load an existing YAML manifest if it exists.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary with previously recorded hashes (empty if none).
    """
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_manifest(manifest: dict, manifest_path: Path) -> None:
    """
    Write the manifest dictionary to a YAML file.

    Args:
        manifest: Mapping of file paths to SHA‑256 hashes.
        manifest_path: Destination path.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=True)

def download_dataset(name: str, config: str | None = None) -> Path:
    """
    Download a HuggingFace dataset and save it as a Parquet file.

    The function loads the full (non‑streaming) dataset, concatenates all
    splits into a single DataFrame, and writes it to `data/raw/<sanitized>.parquet`.

    Args:
        name: Dataset identifier (e.g., "gsm8k").
        config: Optional configuration name (e.g., "main").

    Returns:
        Path to the written Parquet file.
    """
    # Load the dataset (full download)
    if config is not None:
        dataset = load_dataset(name, config, streaming=False)
    else:
        dataset = load_dataset(name, streaming=False)

    # Concatenate all available splits into one DataFrame
    frames = []
    for split in dataset.keys():
        frames.append(dataset[split].to_pandas())
    df = pd.concat(frames, ignore_index=True)

    # Determine output filename
    safe_name = name.replace("/", "_")
    out_path = get_config().data_raw / f"{safe_name}.parquet"

    # Write Parquet
    df.to_parquet(out_path, index=False)
    return out_path

def main() -> None:
    """
    Main entry point executed by `python src/data/download.py`.

    Downloads the three required datasets, records their SHA‑256 hashes,
    and writes a manifest to `state/artifact_hashes.yaml`.
    """
    ensure_directories()
    cfg = get_config()
    manifest_path = cfg.state_dir / "artifact_hashes.yaml"
    manifest = load_manifest(manifest_path)

    # Dataset specifications: (HF identifier, optional config)
    datasets_to_fetch = [
        ("gsm8k", "main"),          # GSM8K (train+test)
        ("math_dataset", None),     # MATH
        ("cais/mmlu", None),        # MMLU‑STEM (full MMLU; downstream code can filter)
    ]

    for ds_name, ds_config in datasets_to_fetch:
        try:
            parquet_path = download_dataset(ds_name, ds_config)
            file_hash = compute_sha256(parquet_path)
            manifest[str(parquet_path)] = file_hash
            print(f"✔ Downloaded {ds_name} → {parquet_path}")
        except Exception as exc:
            print(f"✖ Failed to download {ds_name}: {exc}", file=sys.stderr)
            sys.exit(1)

    # Persist the manifest
    save_manifest(manifest, manifest_path)
    print(f"✅ Manifest written to {manifest_path}")

if __name__ == "__main__":
    main()
