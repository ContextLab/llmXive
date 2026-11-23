import hashlib
import json
import os
import sys
import random
import pathlib
import yaml
import numpy as np
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def download_file(url: str, dest_path: pathlib.Path) -> str:
    """
    Streams a file from the given URL to dest_path while computing its SHA-256 checksum.
    Returns the hexadecimal checksum string.
    """
    import urllib.request

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    with urllib.request.urlopen(url) as response, open(dest_path, "wb") as out_file:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            out_file.write(chunk)
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    log.info(f"Downloaded {url} to {dest_path} (sha256={checksum})")
    return checksum

def write_checksums(checksum_dict: dict):
    """
    Writes a checksums.txt file with one line per entry:
    <filename> <sha256>
    """
    checksums_path = paths.data("raw", "fluordb", "checksums.txt")
    with open(checksums_path, "w") as f:
        for filename, cs in checksum_dict.items():
            f.write(f"{filename} {cs}\n")
    log.info(f"Wrote checksums to {checksums_path}")

def read_checksums() -> dict:
    """
    Reads checksums.txt and returns a mapping filename -> sha256.
    """
    checksums_path = paths.data("raw", "fluordb", "checksums.txt")
    if not checksums_path.is_file():
        raise FileNotFoundError(f"Checksum file not found at {checksums_path}")
    result = {}
    with open(checksums_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 2:
                continue
            filename, cs = parts
            result[filename] = cs
    return result

def verify_checksums(expected: dict):
    """
    Verifies that each file listed in `expected` exists under the same directory
    as the checksum file and that its SHA-256 matches the expected value.
    Raises a RuntimeError on any mismatch.
    """
    base_dir = paths.data("raw", "fluordb")
    for filename, expected_cs in expected.items():
        file_path = base_dir / filename
        if not file_path.is_file():
            raise RuntimeError(f"Expected file {file_path} is missing")
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_cs = sha256.hexdigest()
        if actual_cs != expected_cs:
            raise RuntimeError(
                f"Checksum mismatch for {file_path}: expected {expected_cs}, got {actual_cs}"
            )
    log.info("All checksum verifications passed")

def load_and_set_seeds():
    """
    Loads seed values from code/config/seeds.yaml, sets seeds for Python,
    random, NumPy, and (if available) PyTorch, and writes the mapping to
    results/seeds.json for downstream verification.
    """
    seeds_path = paths.code("config", "seeds.yaml")
    if not seeds_path.is_file():
        raise FileNotFoundError(f"Seed configuration not found at {seeds_path}")

    with open(seeds_path, "r") as f:
        cfg = yaml.safe_load(f)

    # Expected keys: pythonhashseed, random_seed, numpy_seed, torch_seed (optional)
    pythonhashseed = cfg.get("pythonhashseed", 0)
    random_seed = cfg.get("random_seed", 42)
    numpy_seed = cfg.get("numpy_seed", 42)
    torch_seed = cfg.get("torch_seed", None)

    os.environ["PYTHONHASHSEED"] = str(pythonhashseed)
    random.seed(random_seed)
    np.random.seed(numpy_seed)

    try:
        import torch
        if torch_seed is not None:
            torch.manual_seed(torch_seed)
    except ImportError:
        log.warning("torch not installed; skipping torch seed setting")

    # Write out the seeds that were actually set
    out = {
        "pythonhashseed": pythonhashseed,
        "random_seed": random_seed,
        "numpy_seed": numpy_seed,
    }
    if torch_seed is not None:
        out["torch_seed"] = torch_seed

    out_path = paths.results("seeds.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    log.info(f"Wrote seed mapping to {out_path}")

def main():
    """
    Entry point used by the project's seed configuration import side‑effect.
    It simply loads and sets the seeds.
    """
    load_and_set_seeds()
    return 0

if __name__ == "__main__":
    sys.exit(main())
