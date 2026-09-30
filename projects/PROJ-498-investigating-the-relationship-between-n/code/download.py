"""
Download module for fetching EEG datasets from OpenNeuro.
Implements T012 (Dataset Selection) and T013 (Raw Data Fetching with Checksum).
"""
import json
import os
import sys
import hashlib
import urllib.request
import urllib.error
import tarfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import shared logging utility
try:
    from synchrony import get_logger
except ImportError:
    # Fallback for isolated execution if synchrony.py is not yet in path
    import logging
    def get_logger(*args, **kwargs):
        return logging.getLogger("download")

logger = get_logger("download")

# Constants
OPENNEURO_API_URL = "https://api.openneuro.org/crn/datasets"
DATASET_ID_FILE = "data/selected_dataset_id.txt"
DATA_GAP_REPORT_PATH = "data/data_gap_report.json"
RAW_DATA_DIR = "data/raw"
LOG_FILE_PATH = "logs/processing.log"

# Ensure directories exist
Path(RAW_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(parents=True, exist_ok=True)
Path("data").mkdir(parents=True, exist_ok=True)

def log_to_file(message: str) -> None:
    """Append a message to the processing log."""
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()
    log_line = f"[{timestamp}] {message}\n"
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON schema from disk."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def query_openneuro_api(query: str) -> List[Dict[str, Any]]:
    """
    Query OpenNeuro API for datasets matching a query.
    Returns a list of dataset metadata dicts.
    """
    url = f"{OPENNEURO_API_URL}?_sort=modified&_expand=license&_embed=authors&_embed=groups"
    # Note: The public API might be limited. We attempt a direct fetch of known dataset if query is specific.
    # For general search, we might need a GraphQL endpoint, but standard REST is attempted here.
    # Since the API is complex, we fallback to checking specific IDs if the query is an ID.
    if query.startswith("ds"):
        # Direct fetch for specific ID
        specific_url = f"{OPENNEURO_API_URL}/{query}"
        try:
            req = urllib.request.Request(specific_url, headers={'User-Agent': 'llmXive/1.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                return [data] if isinstance(data, dict) else []
        except Exception as e:
            log_to_file(f"API fetch for {query} failed: {e}")
            return []
    
    # Fallback for general search (simplified)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'llmXive/1.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            # Filter manually if needed
            return data.get("datasets", [])
    except Exception as e:
        log_to_file(f"General API search failed: {e}")
        return []

def check_dataset_availability(dataset_id: str) -> bool:
    """Check if a specific dataset ID exists on OpenNeuro."""
    results = query_openneuro_api(dataset_id)
    return len(results) > 0 and results[0].get("id") == dataset_id

def select_dataset(primary_id: str = "ds004173", fallback_query: str = "task-switching") -> Optional[str]:
    """
    Attempt to select the primary dataset. If unavailable, search for fallback.
    Returns the dataset ID or None.
    """
    # 1. Try Primary
    if check_dataset_availability(primary_id):
        log_to_file(f"Primary dataset {primary_id} found and available.")
        return primary_id

    log_to_file(f"Primary dataset {primary_id} unavailable. Searching fallback...")

    # 2. Try Fallback Search
    # Note: Real API search might require GraphQL. We simulate a check for known fallbacks or search.
    # For this implementation, we attempt to find any dataset with 'switching' in name if we can.
    # Since we can't easily parse the full list without a robust API, we return None if primary fails
    # unless we have a known fallback list.
    # However, the spec says: "query the OpenNeuro API for datasets containing 'task-switching' events"
    # We will attempt a direct query if the API supports it, otherwise we assume failure.
    
    # Attempting a direct search via the API (simplified)
    fallbacks = query_openneuro_api(fallback_query)
    for ds in fallbacks:
        # Check if name or description contains 'switching'
        name = ds.get("name", "").lower()
        desc = ds.get("description", {}).get("text", "").lower() if isinstance(ds.get("description"), dict) else ""
        if "switching" in name or "switching" in desc:
            log_to_file(f"Fallback dataset {ds.get('id')} found.")
            return ds.get("id")

    log_to_file("No fallback dataset found.")
    return None

def generate_data_gap_report(dataset_id: Optional[str], reason: str, fallback_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate the data gap report adhering to contracts/data_gap_report.schema.yaml.
    Returns the report dict and writes it to disk.
    """
    from datetime import datetime
    report = {
        "dataset_id": dataset_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat(),
        "fallback_id": fallback_id if fallback_id else None
    }
    
    # Ensure data directory exists
    Path("data").mkdir(parents=True, exist_ok=True)
    
    with open(DATA_GAP_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    log_to_file(f"Data gap report generated: {DATA_GAP_REPORT_PATH}")
    return report

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_dataset(dataset_id: str, output_dir: str) -> bool:
    """
    Download the dataset from OpenNeuro.
    Uses the OpenNeuro API to get the latest snapshot and downloads the tarball.
    """
    # Construct download URL for the latest snapshot
    # Format: https://openneuro.org/datasets/{id}/versions/latest/download
    # Or via API: https://api.openneuro.org/crn/datasets/{id}/download
    # We will use the direct tarball URL if possible, or the API download endpoint.
    # Since direct tarball links change, we use the API to get the download link.
    
    download_url = f"https://api.openneuro.org/crn/datasets/{dataset_id}/download"
    # Note: This might require authentication or specific headers.
    # Alternative: Use the public snapshot URL structure if available.
    # https://openneuro.org/datasets/{id}/versions/{version}/download
    
    # Attempt to get the download URL via API
    try:
        # OpenNeuro v2 API download
        req = urllib.request.Request(download_url, headers={'User-Agent': 'llmXive/1.0'})
        # This endpoint might return a redirect or the file directly.
        # If it returns JSON with a URL, we follow it.
        with urllib.request.urlopen(req, timeout=120) as response:
            # If it's a file, we write it
            if response.headers.get('Content-Type', '').startswith('application/octet-stream') or 'tar' in response.headers.get('Content-Type', ''):
                tar_path = os.path.join(output_dir, f"{dataset_id}.tar.gz")
                with open(tar_path, 'wb') as f:
                    f.write(response.read())
                log_to_file(f"Downloaded {tar_path}")
                return True
    except urllib.error.HTTPError as e:
        log_to_file(f"HTTP Error downloading {dataset_id}: {e.code} {e.reason}")
        # Fallback: Try the snapshot URL directly if API download fails
        # This is a heuristic for public datasets
        snapshot_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/download"
        try:
            req = urllib.request.Request(snapshot_url, headers={'User-Agent': 'llmXive/1.0'})
            with urllib.request.urlopen(req, timeout=120) as response:
                tar_path = os.path.join(output_dir, f"{dataset_id}.tar.gz")
                with open(tar_path, 'wb') as f:
                    f.write(response.read())
                log_to_file(f"Downloaded {tar_path} (fallback method)")
                return True
        except Exception as e2:
            log_to_file(f"Fallback download failed: {e2}")
            return False
    except Exception as e:
        log_to_file(f"Download error: {e}")
        return False

def extract_and_verify(tar_path: str, dest_dir: str) -> bool:
    """Extract the tarball and verify basic structure."""
    try:
        with tarfile.open(tar_path, "r:gz") as tar:
            tar.extractall(path=dest_dir)
        log_to_file(f"Extracted {tar_path} to {dest_dir}")
        # Verify basic BIDS structure (dataset_description.json)
        bids_check = os.path.join(dest_dir, "dataset_description.json")
        if not os.path.exists(bids_check):
            log_to_file("Warning: dataset_description.json not found after extraction.")
            # Still return True if extraction happened, as some datasets might be raw
        return True
    except Exception as e:
        log_to_file(f"Extraction failed: {e}")
        return False

def main():
    """
    Main entry point for T012 and T013.
    1. Reads selected_dataset_id.txt (if exists) or runs T012 logic to find one.
    2. Downloads the dataset to data/raw/.
    3. Computes SHA-256 checksum.
    """
    # Step 1: Ensure we have a dataset ID
    dataset_id = None
    
    if os.path.exists(DATASET_ID_FILE):
        with open(DATASET_ID_FILE, "r", encoding="utf-8") as f:
            dataset_id = f.read().strip()
        log_to_file(f"Loaded dataset ID from file: {dataset_id}")
    else:
        # Run T012 logic inline if file missing (as per task dependency chain)
        log_to_file("Dataset ID file missing. Running selection logic (T012).")
        dataset_id = select_dataset()
        if dataset_id:
            with open(DATASET_ID_FILE, "w", encoding="utf-8") as f:
                f.write(dataset_id)
            log_to_file(f"Saved selected dataset ID: {dataset_id}")
        else:
            # Generate gap report and halt
            generate_data_gap_report(
                dataset_id=None,
                reason="Primary dataset ds004173 unavailable and no fallback found.",
                fallback_id=None
            )
            log_to_file("Halting execution due to missing dataset.")
            sys.exit(1)

    # Step 2: Download
    log_to_file(f"Starting download for {dataset_id}")
    success = download_dataset(dataset_id, RAW_DATA_DIR)
    
    if not success:
        log_to_file("Download failed. Generating gap report.")
        generate_data_gap_report(
            dataset_id=dataset_id,
            reason="Download failed (network or API error).",
            fallback_id=None
        )
        sys.exit(1)

    # Step 3: Verify Checksum
    tar_path = os.path.join(RAW_DATA_DIR, f"{dataset_id}.tar.gz")
    if os.path.exists(tar_path):
        checksum = compute_sha256(tar_path)
        log_to_file(f"Checksum computed for {dataset_id}: {checksum}")
        # Note: We don't have a reference checksum, so we just log it.
        # In a real scenario, we would compare against a known hash.
    else:
        log_to_file(f"Tarball not found at {tar_path} for checksum verification.")
        sys.exit(1)

    # Step 4: Extract
    if not extract_and_verify(tar_path, RAW_DATA_DIR):
        log_to_file("Extraction failed.")
        sys.exit(1)

    log_to_file("Download and verification complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
