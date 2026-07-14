import os
import sys
import logging
import hashlib
import json
import urllib.request
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums(checksum_file):
    """Load checksums from a JSON file."""
    if not os.path.exists(checksum_file):
        return {}
    with open(checksum_file, "r") as f:
        return json.load(f)

def save_checksums(checksums, checksum_file):
    """Save checksums to a JSON file."""
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)

def validate_checksum(filepath, expected_checksum):
    """Validate file checksum."""
    actual_checksum = calculate_sha256(filepath)
    return actual_checksum == expected_checksum

def check_required_columns(df, required_columns):
    """Check if DataFrame has required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Required columns missing: {', '.join(missing)}")
    return True

def download_dataset(url, output_path, expected_checksum=None):
    """Download a dataset from a URL."""
    log_info(f"Attempting to download: {url}")
    try:
        urllib.request.urlretrieve(url, output_path)
        log_info(f"Downloaded to: {output_path}")

        if expected_checksum:
            if validate_checksum(output_path, expected_checksum):
                log_info("Checksum validation passed.")
            else:
                log_error("Checksum validation failed.")
                return False
        return True
    except Exception as e:
        log_error(f"HTTP Error downloading {url}: {e}")
        return False

def main():
    """Main entry point for T005."""
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_file = raw_dir / "sample_behavioral_data.csv"
    checksum_file = raw_dir / "checksums.json"

    # Known valid behavioral dataset source (public, accessible)
    # Using a reliable public sample from a known repository structure
    # If this specific URL is 404, we try a fallback or report failure clearly.
    # For this implementation, we use a direct link to a known valid CSV in a public repo.
    # Note: In a real CI environment, we ensure the URL is reachable.
    # Fallback strategy: Try primary, then fallback.

    sources = [
        {
            "url": "https://raw.githubusercontent.com/psychopy/datasets/main/sample_behavioral_data.csv",
            "expected_checksum": None  # We can validate if we have the checksum
        },
        {
            "url": "https://raw.githubusercontent.com/llmXive/datasets/main/sample_behavioral_data.csv",
            "expected_checksum": None
        }
    ]

    # Load existing checksums if any
    existing_checksums = load_checksums(checksum_file)

    downloaded = False
    for source in sources:
        url = source["url"]
        expected_checksum = source.get("expected_checksum")

        if download_dataset(url, str(output_file), expected_checksum):
            # Save checksum if we have one or calculate it
            if expected_checksum:
                existing_checksums[url] = expected_checksum
            else:
                # Calculate and save actual checksum
                actual_checksum = calculate_sha256(output_file)
                existing_checksums[url] = actual_checksum
                log_info(f"Saved checksum for {url}: {actual_checksum}")
            
            save_checksums(existing_checksums, str(checksum_file))
            downloaded = True
            break

    if not downloaded:
        log_error("Failed to download and validate any known behavioral dataset.")
        log_error("T005 failed. Project cannot proceed without valid behavioral data.")
        sys.exit(1)

    log_info("T005 completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()