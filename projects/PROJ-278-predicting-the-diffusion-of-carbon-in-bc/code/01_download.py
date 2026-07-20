import os
import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional
import requests

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path) -> None:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def main():
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).parent.parent
    data_dir = root / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    url = "https://huggingface.co/datasets/materials-informatics/Melidc/resolve/main/melidc.parquet"
    output_file = data_dir / "melidc.parquet"
    
    if not output_file.exists():
        logger.info(f"Downloading {url}...")
        download_file(url, output_file)
        checksum = compute_sha256(output_file)
        logger.info(f"Downloaded. SHA256: {checksum}")
    else:
        logger.info(f"File already exists: {output_file}")

if __name__ == "__main__":
    main()
