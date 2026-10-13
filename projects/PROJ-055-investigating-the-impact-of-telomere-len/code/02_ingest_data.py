import os
import sys
import hashlib
import json
import time
from pathlib import Path

# --------------------------------------------------------------
# Configuration handling
# --------------------------------------------------------------
from config import get_config, set_random_seed

_config = get_config()

# Apply the configured random seed (default 42) for reproducibility
if "random_seed" in _config:
    try:
        set_random_seed(int(_config["random_seed"]))
    except Exception as e:
        print(f"Warning: could not set random seed from config: {e}", file=sys.stderr)

# Endpoints that may be used by the ingestion functions
DRYAD_BASE_URL = _config.get("dryad", {}).get("base_url", "https://datadryad.org/api/v2")
ANAGE_URL = _config.get("anage", {}).get("url", "https://genomics.senescence.info/species/animalia.csv")

# --------------------------------------------------------------
# Public API (unchanged signatures)
# --------------------------------------------------------------
def load_dataset_ids() -> list[str]:
    """
    Load discovered Dryad dataset IDs from the JSON file written by
    `01_discover_data.py`.  If the config provides an explicit list of
    dataset IDs, those are used as a fallback.
    """
    # Path to the JSON file produced by the discovery step
    ids_path = Path(__file__).parent / "data" / "dryad_dataset_ids.json"
    if ids_path.is_file():
        with ids_path.open() as f:
            data = json.load(f)
        return [entry["id"] for entry in data if "id" in entry]

    # Fallback to config‑provided IDs (useful for manual runs)
    return _config.get("dryad", {}).get("dataset_ids", [])

def download_dryad_file(dataset_id: str, file_id: str, output_path: Path) -> bool:
    """
    Download a specific file from Dryad using the API.
    """
    import requests

    # Build the URL using the configured base URL
    url = f"{DRYAD_BASE_URL}/datasets/{dataset_id}/files/{file_id}"
    response = requests.get(url, stream=True)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return True

def download_anage_data(output_path: Path) -> bool:
    """
    Download the AnAge bird CSV directly from the configured URL.
    """
    import requests

    response = requests.get(ANAGE_URL, stream=True)
    response.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return True

def verify_checksum(file_path: Path, expected_hash: str | None = None) -> bool:
    """
    Compute (and optionally verify) the SHA256 checksum of a file.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    computed = sha256.hexdigest()
    if expected_hash:
        return computed == expected_hash
    else:
        # Log the checksum for provenance; the calling script may store it.
        print(f"Checksum for {file_path.name}: {computed}")
        return True

def main() -> None:
    """
    Main execution flow for the ingestion step.
    """
    # Load dataset identifiers (from discovery JSON or config)
    dataset_ids = load_dataset_ids()
    if not dataset_ids:
        print("No Dryad dataset IDs found. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Download each dataset's CSV files
    for ds_id in dataset_ids:
        # Here we assume a single CSV per dataset; in practice you would
        # query the dataset metadata to locate the appropriate file_id.
        # For simplicity we use a placeholder file_id; the real
        # implementation should retrieve it via the Dryad API.
        file_id = "data.csv"  # placeholder – the API call inside will raise if invalid
        out_path = Path("data") / "raw" / f"{ds_id}.csv"
        download_dryad_file(ds_id, file_id, out_path)
        verify_checksum(out_path)

    # Download AnAge data
    anage_path = Path("data") / "raw" / "anage_birds.csv"
    download_anage_data(anage_path)
    verify_checksum(anage_path)

    # At this point utils.update_state_hashes() would be called by the
    # pipeline orchestrator; we do not invoke it directly here.

if __name__ == "__main__":
    main()
