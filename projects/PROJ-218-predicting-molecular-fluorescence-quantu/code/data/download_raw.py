import hashlib
import json
import os
import sys
import random
import pathlib
import requests
import yaml
import numpy as np
import torch
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def download_file(url: str, dest_path: pathlib.Path) -> str:
    """
    Streams a file from url to dest_path while computing its SHA-256.
    """
    log.info(f"Downloading {url} to {dest_path}")
    sha256_hash = hashlib.sha256()
    
    # Ensure directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with requests.get(url, stream=True, allow_redirects=True) as r:
        r.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def write_checksums(checksum_dict: dict):
    """
    Writes a checksums.txt file with one line per entry: <filename> <sha256>.
    """
    out_path = paths.data("raw", "checksums.txt")
    with open(out_path, "w") as f:
        for filename, digest in checksum_dict.items():
            f.write(f"{filename} {digest}\n")

def read_checksums() -> dict:
    """
    Reads checksums.txt and returns a mapping filename -> sha256.
    """
    in_path = paths.data("raw", "checksums.txt")
    if not in_path.exists():
        return {}
    
    checksums = {}
    with open(in_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                checksums[parts[0]] = parts[1]
    return checksums

def verify_checksums(expected: dict):
    """
    Verifies that the SHA-256 of each file on disk matches the expected value.
    """
    for filename, expected_digest in expected.items():
        file_path = paths.data("raw", filename)
        if not file_path.exists():
            raise ValueError(f"File {filename} not found for checksum verification")
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        
        actual_digest = sha256_hash.hexdigest()
        if actual_digest != expected_digest:
            raise ValueError(f"Checksum mismatch for {filename}: expected {expected_digest}, got {actual_digest}")

def load_and_set_seeds():
    """
    Loads seed values from code/config/seeds.yaml, sets seeds, 
    and writes the seed mapping to results/seeds.json.
    """
    seed_file = paths.path("code", "config", "seeds.yaml")
    with open(seed_file, "r") as f:
        seeds = yaml.safe_load(f)
    
    # Set seeds
    os.environ["PYTHONHASHSEED"] = str(seeds.get("pythonhashseed", 0))
    random.seed(seeds.get("random_seed", 42))
    np.random.seed(seeds.get("numpy_seed", 42))
    torch.manual_seed(seeds.get("torch_seed", 42))
    
    # Record seeds
    out_json = paths.results("seeds.json")
    with open(out_json, "w") as f:
        json.dump(seeds, f, indent=2)
    
    log.info(f"Seeds initialized and recorded to {out_json}")

def main():
    # This is a utility module; main is provided for completeness
    # but the pipeline uses run_t001_download_and_seed.py
    pass
