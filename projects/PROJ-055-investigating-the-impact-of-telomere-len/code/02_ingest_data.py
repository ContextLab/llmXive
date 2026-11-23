"""
02_ingest_data.py

Downloads raw CSV files from Dryad (using the DOIs discovered by
01_discover_data.py) and the AnAge bird dataset.  For each file a
SHA‑256 checksum file ``<filename>.sha256`` is written alongside the
downloaded data.
"""

import sys
import json
import hashlib
import requests
from pathlib import Path
from typing import Optional, List

import yaml
from utils import generate_checksum, update_state_file

# ------------------------------------------------------------------
# Load configuration (no hard‑coded URLs or seeds)
# ------------------------------------------------------------------
CONFIG_PATH = Path("code") / "config.yaml"

def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

_cfg = load_config()
DRYAD_API_BASE = _cfg.get("dryad_api_base", "https://datadryad.org/api/v2")
ANAGE_URL = _cfg.get("anage_url")
RANDOM_SEED = int(_cfg.get("random_seed", 42))
CHUNK_SIZE = int(_cfg.get("chunk_size", 8192))

# ------------------------------------------------------------------
# Helper utilities
# ------------------------------------------------------------------
def _discover_csv_file_id(dataset_id: str) -> Optional[str]:
    """
    Query the Dryad API for a dataset's file list and return the first
    file identifier that ends with '.csv'. Returns None if no CSV is found.
    """
    url = f"{DRYAD_API_BASE}/datasets/{dataset_id}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    for f in data.get("files", []):
        fname = f.get("filename") or f.get("name")
        if fname and fname.lower().endswith(".csv"):
            return f.get("id") or f.get("file_id")
    return None

def download_dryad_file(dataset_id: str, file_id: Optional[str], out_path: Path) -> None:
    """
    Download a CSV file from a Dryad dataset.  Raises on any failure.
    """
    if file_id is None:
        file_id = _discover_csv_file_id(dataset_id)
        if not file_id:
            raise FileNotFoundError(f"No CSV found in Dryad dataset {dataset_id}")

    url = f"{DRYAD_API_BASE}/datasets/{dataset_id}/files/{file_id}"
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    # Write checksum file
    checksum = generate_checksum(out_path)
    (out_path.with_suffix(out_path.suffix + ".sha256")).write_text(checksum)

def download_anage_data(out_path: Path) -> None:
    """
    Download the AnAge bird CSV.
    """
    with requests.get(ANAGE_URL, stream=True, timeout=60) as r:
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    checksum = generate_checksum(out_path)
    (out_path.with_suffix(out_path.suffix + ".sha256")).write_text(checksum)

# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def load_dataset_ids() -> List[str]:
    """
    Load the list of Dryad dataset IDs discovered by 01_discover_data.py.
    Falls back to any IDs manually listed in the config file.
    """
    json_path = Path("data") / "raw" / "dryad_dataset_ids.json"
    if json_path.is_file():
        with json_path.open("r", encoding="utf-8") as jf:
            data = json.load(jf)
        return [entry["id"] for entry in data if "id" in entry]

    # Fallback to config‑provided list (may be empty)
    return _cfg.get("dataset_ids", [])

def main() -> None:
    """
    Execute the ingestion workflow.
    """
    dataset_ids = load_dataset_ids()
    if not dataset_ids:
        print("Warning: No Dryad dataset IDs discovered; only AnAge will be downloaded.", file=sys.stderr)

    # Download each Dryad CSV
    for ds_id in dataset_ids:
        out_file = Path("data") / "raw" / f"{ds_id}.csv"
        try:
            download_dryad_file(ds_id, None, out_file)
            print(f"Downloaded Dryad dataset {ds_id} to {out_file}")
        except Exception as e:
            print(f"Failed to download dataset {ds_id}: {e}", file=sys.stderr)

    # Download AnAge data
    anage_path = Path("data") / "raw" / "anage_birds.csv"
    try:
        download_anage_data(anage_path)
        print(f"Downloaded AnAge data to {anage_path}")
    except Exception as e:
        print(f"Failed to download AnAge data: {e}", file=sys.stderr)
        sys.exit(1)

    # Record a simple state hash for provenance
    hash_map = {}
    for p in Path("data") / "raw" .glob("*"):
        if p.is_file():
            hash_map[str(p.relative_to(Path.cwd()))] = generate_checksum(p)
    update_state_file(hash_map)

if __name__ == "__main__":
    main()
