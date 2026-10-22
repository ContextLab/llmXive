"""
verify_checksum.py

This script runs the full end‑to‑end pipeline for a 50‑clip subset,
captures the printed summary table, computes its SHA‑256 checksum,
and verifies that it matches the checksum of the generated
``descriptors_subset.csv`` file.

If the checksums differ the script exits with a non‑zero status,
causing the CI verification to fail.
"""

import subprocess
import hashlib
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
    subset and capture its stdout.

    Returns:
        The raw stdout output as bytes.
    """
    cmd = [
        sys.executable,
        "-m",
        "src.pipeline.run_all",
        "--subset",
        "50",
    ]
    log.info("Running pipeline: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    if result.stderr:
        log.debug("Pipeline stderr: %s", result.stderr.decode())
    return result.stdout

def _load_descriptor_subset() -> Path:
    """
    Return the path to the generated ``descriptors_subset.csv`` file.
    The pipeline writes this file under ``data/processed``.
    """
    csv_path = paths.data("processed", "descriptors_subset.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"Descriptor subset CSV not found at expected location: {csv_path}"
        )
    return csv_path

def main() -> None:
    # 1. Run the pipeline and capture the printed table.
    stdout_bytes = _run_pipeline()

    # 2. Compute SHA‑256 of the printed table.
    table_hash = _sha256_bytes(stdout_bytes)
    log.info("SHA‑256 of printed summary table: %s", table_hash)

    # 3. Compute SHA‑256 of the descriptors_subset CSV file.
    csv_path = _load_descriptor_subset()
    csv_bytes = csv_path.read_bytes()
    csv_hash = _sha256_bytes(csv_bytes)
    log.info("SHA‑256 of %s: %s", csv_path, csv_hash)

    # 4. Compare the two hashes.
    if table_hash != csv_hash:
        log.error(
            "Checksum mismatch: table (%s) != descriptors_subset.csv (%s)",
            table_hash,
            csv_hash,
        )
        # Exit with non‑zero status to signal failure.
        sys.exit(1)

    log.info("Checksum verification succeeded: both hashes match.")
    # Successful exit.
    sys.exit(0)

if __name__ == "__main__":
    main()
