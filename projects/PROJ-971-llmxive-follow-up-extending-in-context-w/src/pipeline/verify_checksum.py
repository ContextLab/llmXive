"""
verify_checksum.py

Executes the minimal end‑to‑end pipeline, captures its stdout table,
computes its SHA‑256 checksum, and compares it to the checksum of the
generated ``descriptors_subset.csv`` file.  If the checksums differ the
script exits with a non‑zero status, causing CI to fail.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _sha256_bytes(data: bytes) -> str:
    """Return the hex SHA‑256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()

def _run_pipeline() -> bytes:
    """
    Execute the full pipeline (``src.pipeline.run_all``) for a 50‑clip
    subset and capture its stdout as raw bytes.
    """
    cmd = [sys.executable, "-m", "src.pipeline.run_all", "--subset", "50"]
    log.info("Running pipeline: %s", " ".join(cmd))
    # ``check_output`` raises CalledProcessError on non‑zero exit.
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return output

def _load_descriptor_subset() -> Path:
    """
    Return the path to the generated ``descriptors_subset.csv`` file.
    The pipeline writes this file under ``data/processed``.
    """
    return paths.data("processed", "descriptors_subset.csv")

def main() -> None:
    # 1. Run the pipeline and capture its printed table.
    stdout_bytes = _run_pipeline()
    stdout_hash = _sha256_bytes(stdout_bytes)
    log.info("SHA‑256 of pipeline stdout table: %s", stdout_hash)

    # 2. Load the subset CSV and compute its SHA‑256 checksum.
    subset_path = _load_descriptor_subset()
    if not subset_path.is_file():
        log.error("Descriptor subset CSV not found at %s", subset_path)
        sys.exit(1)

    with subset_path.open("rb") as f:
        csv_bytes = f.read()
    csv_hash = _sha256_bytes(csv_bytes)
    log.info("SHA‑256 of %s: %s", subset_path, csv_hash)

    # 3. Compare the two checksums.
    if stdout_hash != csv_hash:
        log.error(
            "Checksum mismatch: stdout %s != CSV %s", stdout_hash, csv_hash
        )
        sys.exit(1)

    log.info("Checksum verification succeeded.")
    print(f"Checksum OK: {stdout_hash}")

if __name__ == "__main__":
    main()
