import os
import hashlib
import subprocess
import pytest
from pathlib import Path

from config import get_results_dir

def get_file_hash(filepath: str) -> str:
    """Calculate MD5 hash of a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def verify_reproducibility() -> bool:
    """
    Run runner.py --full twice and verify that the output hash is identical.
    Returns True if hashes match, False otherwise.
    """
    results_dir = get_results_dir()
    log_path = os.path.join(results_dir, "simulation_logs.json")

    # Clean up previous run if exists
    if os.path.exists(log_path):
        os.remove(log_path)

    # Run 1
    result1 = subprocess.run(
        ["python", "code/runner.py", "--full"],
        capture_output=True,
        text=True,
    )
    if result1.returncode != 0:
        raise RuntimeError(f"First run failed: {result1.stderr}")

    if not os.path.exists(log_path):
        raise FileNotFoundError("Log file not created after first run.")

    hash1 = get_file_hash(log_path)

    # Run 2
    result2 = subprocess.run(
        ["python", "code/runner.py", "--full"],
        capture_output=True,
        text=True,
    )
    if result2.returncode != 0:
        raise RuntimeError(f"Second run failed: {result2.stderr}")

    hash2 = get_file_hash(log_path)

    return hash1 == hash2

def test_reproducibility():
    """Pytest wrapper for verify_reproducibility."""
    assert verify_reproducibility(), "Reproducibility check failed: outputs differ between runs."
