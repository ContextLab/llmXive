"""
Dataset Downloader for Socratic Transformers Project.

Downloads GSM8K, MATH (prealgebra subset), and MMLU‑STEM datasets from HuggingFace,
writes each as a Parquet file into ``data/raw/`` (preserving the expected
filenames), and records SHA‑256 checksums in ``state/artifact_hashes.yaml``.
The script fails loudly if any download or file operation cannot be completed.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure the project root (the ``code`` directory) is on ``sys.path`` so that
# relative imports work regardless of the current working directory.
project_root = Path(__file__).resolve().parents[3]  # code/
sys.path.insert(0, str(project_root))

import pandas as pd
from huggingface_hub import hf_hub_download
import yaml

# ----------------------------------------------------------------------
# Configuration for each dataset we need to download.
# ----------------------------------------------------------------------
DATASET_CONFIGS = [
    {
        "name": "gsm8k",
        "hf_id": "openai/gsm8k",
        "config": "main",
        "split": "train",
        "output_file": "gsm8k.parquet",
    },
    {
        "name": "math",
        "hf_id": "hendrycks/math",
        "config": "prealgebra",  # a manageable subset for quick runs
        "split": "train",
        "output_file": "math.parquet",
    },
    {
        "name": "mmlu_stem",
        "hf_id": "cais/mmlu",
        "config": "stem",
        "split": "train",
        "output_file": "mmlu_stem.parquet",
    },
]

# ----------------------------------------------------------------------
# Directory layout (all paths are anchored at the ``code`` directory).
# ----------------------------------------------------------------------
RAW_DATA_DIR = project_root / "data" / "raw"
STATE_DIR = project_root / "state"
MANIFEST_FILE = STATE_DIR / "artifact_hashes.yaml"

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def ensure_data_dirs() -> None:
    """Create ``data/raw`` and ``state`` directories if they do not exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_file_hash(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def load_manifest() -> Dict[str, Any]:
    """Load the existing manifest (YAML) if present; otherwise return {}."""
    if MANIFEST_FILE.is_file():
        with MANIFEST_FILE.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Write ``manifest`` to ``state/artifact_hashes.yaml`` in deterministic order."""
    with MANIFEST_FILE.open("w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)

# ----------------------------------------------------------------------
# Core download logic (uses huggingface_hub to avoid pyarrow dependency)
# ----------------------------------------------------------------------
def download_dataset(dataset_cfg: Dict[str, Any]) -> Optional[Path]:
    """
    Download a dataset file from HuggingFace, convert it to a Pandas DataFrame,
    write it as a Parquet file, and return the path to that file.

    Parameters
    ----------
    dataset_cfg: dict
        Dictionary containing ``hf_id``, ``config``, ``split`` and ``output_file``.

    Returns
    -------
    pathlib.Path | None
        Path to the written Parquet file, or ``None`` if the download failed.
    """
    hf_id = dataset_cfg["hf_id"]
    config_name = dataset_cfg["config"]
    split = dataset_cfg["split"]
    output_name = dataset_cfg["output_file"]

    print(f"Downloading {hf_id} (config={config_name}, split={split}) ...")

    # Build the filename inside the repo.
    # For the default ``main`` config the file is ``train.jsonl``.
    # For other configs the file lives under ``{config}/train.jsonl``.
    if config_name == "main":
        filename = f"{split}.jsonl"
    else:
        filename = f"{config_name}/{split}.jsonl"

    try:
        # Download the raw file to a temporary location.
        local_path = hf_hub_download(
            repo_id=hf_id,
            filename=filename,
            repo_type="dataset",
            # Use the default revision (usually 'main')
        )
    except Exception as exc:
        print(f"ERROR: Failed to download {hf_id}/{filename}: {exc}", file=sys.stderr)
        raise

    # Load into a DataFrame.  Most of the target datasets provide JSONL.
    try:
        if local_path.endswith(".jsonl"):
            df = pd.read_json(local_path, lines=True)
        elif local_path.endswith(".csv"):
            df = pd.read_csv(local_path)
        else:
            raise ValueError(f"Unsupported file extension for {local_path}")
    except Exception as exc:
        print(f"ERROR: Failed to parse downloaded file {local_path}: {exc}", file=sys.stderr)
        raise

    output_path = RAW_DATA_DIR / output_name
    df.to_parquet(output_path, index=False)
    print(f"Saved {output_path}")
    return output_path

def download_all_datasets() -> List[Path]:
    """Iterate over ``DATASET_CONFIGS`` and download each one."""
    ensure_data_dirs()
    downloaded: List[Path] = []
    for cfg in DATASET_CONFIGS:
        path = download_dataset(cfg)
        if path:
            downloaded.append(path)
    return downloaded

# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the full download + manifest generation pipeline."""
    print("=== Starting dataset download ===")
    try:
        files = download_all_datasets()
        if not files:
            print("ERROR: No datasets were downloaded.", file=sys.stderr)
            sys.exit(1)

        manifest = load_manifest()
        for fp in files:
            rel_path = str(fp.relative_to(project_root))
            manifest[rel_path] = {
                "hash": compute_file_hash(fp),
                "algorithm": "sha256",
                "size_bytes": fp.stat().st_size,
            }
            print(f"Hashed {rel_path}")

        save_manifest(manifest)
        print(f"Manifest written to {MANIFEST_FILE}")

    except Exception as exc:
        print(f"CRITICAL: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
