"""
download_data.py

Fetches the verified 316L LPBF dataset from the canonical Zenodo source.
Validates material type, downloads the full file, computes checksum,
and updates state.yaml.
"""

import os
import sys
import hashlib
import logging
import json
import urllib.request
import urllib.error
from pathlib import Path

# Project root (assumed to be one level up from code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_FILE = PROJECT_ROOT / "state.yaml"

# Zenodo Record ID for the verified 316L dataset
ZENODO_RECORD_ID = "6826006"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

# Expected material string in metadata
EXPECTED_MATERIAL = "316L"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("llmXive_pipeline")


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def fetch_record_metadata(record_id: str) -> dict:
    """Fetch metadata from Zenodo API for a given record ID."""
    url = f"https://zenodo.org/api/records/{record_id}"
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch metadata from Zenodo: {e}")
        raise RuntimeError(f"Network error fetching metadata: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from Zenodo: {e}")
        raise RuntimeError(f"Invalid JSON from Zenodo: {e}")


def verify_material_type(metadata: dict) -> None:
    """
    Verify that the dataset metadata indicates 316L Stainless Steel.
    Raises ValueError if material mismatch is detected.
    """
    logger.info("Verifying material type is 316L")

    # Check description
    description = metadata.get("metadata", {}).get("description", "").lower()
    title = metadata.get("metadata", {}).get("title", "").lower()

    # Look for "316L" or "316L stainless steel"
    if "316l" not in description and "316l" not in title:
        # Also check keywords
        keywords = [kw.get("value", "").lower() for kw in metadata.get("metadata", {}).get("keywords", [])]
        if not any("316l" in kw for kw in keywords):
            raise ValueError(
                f"Dataset does not appear to be for 316L stainless steel. "
                f"Title: {title}, Description: {description[:100]}..."
            )

    logger.info("Material type verified: 316L Stainless Steel")


def get_download_url(metadata: dict) -> str:
    """Extract the direct download URL for the CSV file from metadata."""
    files = metadata.get("files", [])
    if not files:
        # Try to find in 'links' if files array is empty in newer API
        links = metadata.get("links", {})
        if "self" in links:
            return links["self"]
        raise ValueError("No files found in Zenodo record metadata.")

    # Find the CSV file
    for f in files:
        if f.get("key", "").endswith(".csv"):
            return f["links"]["self"]

    # Fallback: use the first file if no CSV found (should not happen for verified dataset)
    logger.warning("No CSV file found, using first available file.")
    return files[0]["links"]["self"]


def download_file(url: str, output_path: Path) -> None:
    """Download a file from URL to output_path with progress logging."""
    logger.info(f"Downloading dataset from: {url}")
    logger.info(f"Saving to: {output_path}")

    try:
        with urllib.request.urlopen(url, timeout=300) as response:
            total_size = int(response.getheader("Content-Length", 0))
            downloaded = 0
            block_size = 8192

            with open(output_path, "wb") as out_file:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")

        logger.info("Download completed successfully.")
    except urllib.error.URLError as e:
        logger.error(f"Download failed: {e}")
        raise RuntimeError(f"Failed to download file: {e}")
    except OSError as e:
        logger.error(f"File write error: {e}")
        raise RuntimeError(f"Failed to write file: {e}")


def update_state_with_checksum(checksum: str, filename: str) -> None:
    """Update state.yaml with the new checksum for the downloaded file."""
    import yaml

    if not STATE_FILE.exists():
        logger.warning("state.yaml not found. Creating new state file.")
        state_data = {"artifacts": {}}
    else:
        with open(STATE_FILE, "r") as f:
            state_data = yaml.safe_load(f) or {"artifacts": {}}

    # Update or add artifact entry
    state_data["artifacts"]["raw_dataset"] = {
        "filename": filename,
        "checksum": checksum,
        "source_url": ZENODO_API_URL,
        "record_id": ZENODO_RECORD_ID
    }

    with open(STATE_FILE, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state.yaml with checksum for {filename}")


def main() -> int:
    """Main entry point for data download."""
    logger.info("Starting 316L LPBF dataset download")

    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Fetch metadata
    logger.info(f"Fetching metadata from Zenodo record {ZENODO_RECORD_ID}")
    try:
        metadata = fetch_record_metadata(ZENODO_RECORD_ID)
    except Exception as e:
        logger.error(f"Failed to fetch metadata: {e}")
        return 1

    # Step 2: Verify material type (T000 Gate)
    try:
        verify_material_type(metadata)
    except ValueError as e:
        logger.error(f"Material verification failed: {e}")
        return 1

    # Step 3: Get download URL
    try:
        download_url = get_download_url(metadata)
    except ValueError as e:
        logger.error(f"Failed to get download URL: {e}")
        return 1

    # Step 4: Download the file
    # Determine filename from URL or use default
    filename = os.path.basename(download_url.split("?")[0])
    if not filename.endswith(".csv"):
        filename = "316L_lpbf_dataset.csv"

    output_path = DATA_RAW_DIR / filename

    # Remove existing file if present (to ensure fresh download)
    if output_path.exists():
        logger.info(f"Removing existing file: {output_path}")
        output_path.unlink()

    try:
        download_file(download_url, output_path)
    except RuntimeError as e:
        logger.error(f"Download failed: {e}")
        return 1

    # Step 5: Compute checksum
    checksum = compute_file_hash(output_path)
    logger.info(f"Computed checksum: {checksum}")

    # Step 6: Update state.yaml
    try:
        update_state_with_checksum(checksum, filename)
    except Exception as e:
        logger.error(f"Failed to update state.yaml: {e}")
        return 1

    logger.info("Data download and verification completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())