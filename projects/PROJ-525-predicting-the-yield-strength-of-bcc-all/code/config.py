import os
from pathlib import Path
import hashlib
import json
from typing import List, Tuple
import random
import numpy as np

# Project root relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent

# Directory paths
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_LOGS_DIR = BASE_DIR / "data" / "logs"
FIGURES_DIR = BASE_DIR / "figures"
REPORTS_DIR = BASE_DIR / "reports"
CODE_DIR = BASE_DIR / "code"

# Random seed for reproducibility
RANDOM_SEED = 42

# CI Resource limits
MAX_MEMORY_GB = 14
MAX_DISK_GB = 30

# Initialize random seeds globally
def set_global_seed(seed: int = RANDOM_SEED) -> None:
    """Set random seeds for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    # Note: If torch/tensorflow are added later, their seeds should be set here too

def ensure_dirs():
    """Create required directory structure if they don't exist."""
    dirs = [
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_LOGS_DIR,
        FIGURES_DIR,
        REPORTS_DIR,
        CODE_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    return dirs

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> List[Tuple[str, str]]:
    """Compute SHA-256 checksums for all files in a directory."""
    checksums = []
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file() and file_path.name != ".gitkeep":
            checksum = compute_file_checksum(file_path)
            relative_path = file_path.relative_to(dir_path)
            checksums.append((str(relative_path), checksum))
    return checksums

def save_checksums(checksums: List[Tuple[str, str]], output_path: Path):
    """Save checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> List[Tuple[str, str]]:
    """Load checksums from a JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    return [(item[0], item[1]) for item in data]

def verify_checksums(dir_path: Path, checksum_file: Path) -> bool:
    """Verify file checksums against a stored checksum file."""
    stored_checksums = load_checksums(checksum_file)
    current_checksums = compute_directory_checksum(dir_path)
    
    if len(stored_checksums) != len(current_checksums):
        print(f"Checksum mismatch: expected {len(stored_checksums)} files, found {len(current_checksums)}")
        return False
    
    for (stored_file, stored_hash), (current_file, current_hash) in zip(stored_checksums, current_checksums):
        if stored_file != current_file or stored_hash != current_hash:
            print(f"Checksum mismatch for {stored_file}: expected {stored_hash}, got {current_hash}")
            return False
    
    print("All checksums verified successfully.")
    return True

# Initialize seeds on import to ensure reproducibility for any downstream code
set_global_seed(RANDOM_SEED)