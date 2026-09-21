import os
from pathlib import Path
import hashlib
import json
from typing import List, Tuple
import random

# --- Environment Configuration Management ---
# Determines if running in a CI environment or locally to adjust paths and limits.

def is_ci_environment() -> bool:
    """
    Detects if the code is running in a Continuous Integration environment.
    Checks common CI environment variables (CI, GITHUB_ACTIONS, GITLAB_CI, etc.).
    """
    ci_vars = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI', 'CIRCLECI', 'JENKINS_URL', 'TRAVIS']
    return any(os.environ.get(var) == 'true' for var in ci_vars)

def get_base_path() -> Path:
    """
    Returns the base path for the project.
    In CI, this is typically the workspace root.
    Locally, this is the directory containing this config file.
    """
    if is_ci_environment():
        # In CI, the workspace is often set via a specific env var, default to current dir
        return Path(os.getcwd())
    else:
        # For local development, assume the project root is the parent of 'code/'
        return Path(__file__).resolve().parent.parent

def get_data_path() -> Path:
    """
    Returns the path to the data directory.
    """
    return get_base_path() / "data"

def get_raw_data_path() -> Path:
    """
    Returns the path to the raw data directory.
    """
    return get_data_path() / "raw"

def get_processed_data_path() -> Path:
    """
    Returns the path to the processed data directory.
    """
    return get_data_path() / "processed"

def get_logs_path() -> Path:
    """
    Returns the path to the logs directory.
    """
    return get_data_path() / "logs"

def get_reports_path() -> Path:
    """
    Returns the path to the reports directory.
    """
    return get_base_path() / "reports"

def get_specs_path() -> Path:
    """
    Returns the path to the specs directory.
    """
    return get_base_path() / "specs"

def get_state_path() -> Path:
    """
    Returns the path to the state directory.
    """
    return get_base_path() / "state" / "projects" / "PROJ-525-predicting-the-yield-strength-of-bcc-all"

# --- Resource Limits (CI vs Local) ---
# Adjusts resource constraints based on the environment.

def get_resource_limits() -> dict:
    """
    Returns resource limits (RAM, CPU, Disk) based on the environment.
    CI environments often have stricter limits or specific configurations.
    """
    if is_ci_environment():
        # Conservative defaults for CI to prevent OOM
        return {
            "max_ram_gb": 14,
            "max_disk_gb": 20,
            "max_workers": 2, # Often 2 cores in free tiers
            "timeout_seconds": 3600
        }
    else:
        # Generous defaults for local development
        return {
            "max_ram_gb": 32,
            "max_disk_gb": 100,
            "max_workers": 8,
            "timeout_seconds": 7200
        }

# --- Existing Functions (Preserved from previous tasks) ---

def set_global_seed(seed: int = 42) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    # Note: numpy and other libs should be seeded in their respective modules
    # if they are imported.

def ensure_dirs() -> None:
    """Creates necessary directories if they don't exist."""
    dirs = [
        get_raw_data_path(),
        get_processed_data_path(),
        get_logs_path(),
        get_reports_path(),
        get_state_path(),
        get_specs_path()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def compute_file_checksum(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> str:
    """Computes a combined checksum for all files in a directory."""
    combined_hash = hashlib.sha256()
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            combined_hash.update(rel_path.as_posix().encode())
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    combined_hash.update(byte_block)
    return combined_hash.hexdigest()

def save_checksums(checksums: dict, output_path: Path) -> None:
    """Saves checksums to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def load_checksums(input_path: Path) -> dict:
    """Loads checksums from a JSON file."""
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_checksums(checksums: dict, base_path: Path) -> bool:
    """Verifies files against stored checksums."""
    for file_rel_path, expected_checksum in checksums.items():
        file_path = base_path / file_rel_path
        if not file_path.exists():
            print(f"Missing file: {file_path}")
            return False
        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum != expected_checksum:
            print(f"Checksum mismatch for {file_path}")
            return False
    return True
