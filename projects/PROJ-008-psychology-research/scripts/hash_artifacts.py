"""
Artifact hashing utility for Constitution Principle V (Data Integrity).

This script computes SHA-256 hashes for all data artifacts in the data/ directory
and writes them to data/hashes.txt for reproducibility verification.
"""
import hashlib
import os
from pathlib import Path
from datetime import datetime
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_all_artifacts(data_dir: Path, output_file: Path) -> None:
    """Hash all files in data directory and write to output file."""
    hashes = []
    
    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(('.csv', '.log', '.json', '.yaml', '.png')):
                file_path = Path(root) / file
                file_hash = compute_file_hash(file_path)
                rel_path = file_path.relative_to(data_dir.parent)
                hashes.append(f"{file_hash}  {rel_path}")
                logger.info(f"Hashed: {rel_path} -> {file_hash[:16]}...")
    
    # Sort hashes for reproducibility
    hashes.sort()
    
    # Write to output file with timestamp
    with open(output_file, "w") as f:
        f.write(f"# Artifact Hashes generated at {datetime.utcnow().isoformat()}Z\n")
        f.write("# Constitution Principle V: Data Integrity Verification\n")
        f.write("# Format: <sha256_hash>  <relative_path>\n\n")
        for line in hashes:
            f.write(line + "\n")
    
    logger.info(f"Hash file written to: {output_file}")
    logger.info(f"Total artifacts hashed: {len(hashes)}")

def main():
    """Entry point for artifact hashing."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_file = data_dir / "hashes.txt"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return 1
    
    try:
        hash_all_artifacts(data_dir, output_file)
        return 0
    except Exception as e:
        logger.error(f"Failed to hash artifacts: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
