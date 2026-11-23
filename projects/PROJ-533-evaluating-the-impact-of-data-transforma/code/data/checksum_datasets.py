"""
Checksum utility for the data transformation pipeline.
Provides functionality to compute SHA-256 hashes for dataset files.
"""
import hashlib
import logging
import csv
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
    Returns:
        The hex string of the SHA-256 hash.
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def write_checksums_csv(checksums: List[Dict[str, str]], output_path: Path = Path("data/checksums.csv")) -> None:
    """
    Write a list of checksums to a CSV file.
    
    Args:
        checksums: List of dicts with keys 'dataset_id' and 'checksum'.
        output_path: Path to the output CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset_id", "checksum"])
        writer.writeheader()
        writer.writerows(checksums)

def main() -> None:
    """
    Batch process all files in data/raw and write checksums.csv.
    """
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        log.error("Raw directory does not exist.")
        return

    checksums = []
    for fp in raw_dir.glob("*"):
        if fp.is_file():
            ds_id = fp.stem.replace("openml_", "").replace("uci_", "")
            checksums.append({
                "dataset_id": ds_id,
                "checksum": compute_sha256(fp)
            })
    
    write_checksums_csv(checksums)
    log.info(f"Computed checksums for {len(checksums)} files.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
