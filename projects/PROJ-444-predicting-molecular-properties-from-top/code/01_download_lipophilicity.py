import hashlib
import logging
import sys
import requests
from pathlib import Path

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )
    return logging.getLogger("download_lipophilicity")

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    logger = setup_logging()
    
    url = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/lipophilicity.csv"
    raw_dir = Path("data/raw")
    raw_path = raw_dir / "lipophilicity.csv"
    checksums_path = Path("data/checksums.txt")

    # 1. Ensure directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)

    # 2. Download the dataset
    logger.info(f"Downloading Lipophilicity dataset from {url}...")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with raw_path.open("wb") as f:
            f.write(response.content)
        logger.info(f"Successfully saved dataset to {raw_path}")
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        sys.exit(1)

    # 3. Compute checksum
    checksum = compute_sha256(raw_path)
    logger.info(f"Computed SHA-256: {checksum}")

    # 4. Write to checksums.txt in the EXACT format required by T001a:
    # "lipophilicity.csv <checksum>"
    # We use a temporary set to avoid duplicate entries if the script is rerun,
    # but we ensure the format is exactly as requested.
    existing_lines = []
    if checksums_path.exists():
        with checksums_path.open("r") as f:
            existing_lines = f.readlines()

    # Remove any existing lines for lipophilicity.csv to avoid duplicates
    filtered_lines = [
        line for line in existing_lines 
        if not line.strip().startswith("lipophilicity.csv")
    ]
    
    # Append the new correct format line
    filtered_lines.append(f"lipophilicity.csv {checksum}\n")

    with checksums_path.open("w") as f:
        f.writelines(filtered_lines)
    
    logger.info(f"Updated {checksums_path} with format: lipophilicity.csv {checksum}")

if __name__ == "__main__":
    main()