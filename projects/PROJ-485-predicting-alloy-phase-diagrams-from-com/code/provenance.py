"""
Provenance generation utilities.
Generates a JSON file describing SHA‑256 checksums of all files
in the ``data/raw`` directory and a combined checksum file.
"""
import os
import json
import hashlib
from typing import Dict

from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)


def compute_sha256(filepath: str) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_provenance(raw_dir: str = "data/raw",
                       provenance_path: str = "data/provenance.json",
                       combined_checksum_path: str = "data/raw/checksum.sha256") -> None:
    """
    Scan ``raw_dir`` for files, compute their SHA‑256 checksums,
    write a JSON provenance report, and write a combined checksum file.

    The JSON format is:
        {
            "files": {
                "<relative_path>": "<sha256>",
                ...
            },
            "generated_at": "<ISO‑8601 timestamp>"
        }
    """
    if not os.path.isdir(raw_dir):
        log_error(logger, f"Raw data directory does not exist: {raw_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    provenance: Dict[str, Dict] = {"files": {}, "generated_at": None}

    for root, _, files in os.walk(raw_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, raw_dir)
            try:
                checksum = compute_sha256(fpath)
                provenance["files"][rel_path] = checksum
                log_info(logger, f"Computed checksum for {rel_path}: {checksum}")
            except Exception as e:
                log_error(logger, f"Failed to checksum {rel_path}: {e}")
                raise

    from datetime import datetime
    provenance["generated_at"] = datetime.utcnow().isoformat() + "Z"

    # Write JSON provenance
    os.makedirs(os.path.dirname(provenance_path), exist_ok=True)
    with open(provenance_path, "w") as out_f:
        json.dump(provenance, out_f, indent=2)
    log_info(logger, f"Provenance written to {provenance_path}")

    # Write combined checksum (concatenation of sorted individual checksums)
    combined = "".join(
        checksum
        for _, checksum in sorted(provenance["files"].items())
    )
    combined_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    os.makedirs(os.path.dirname(combined_checksum_path), exist_ok=True)
    with open(combined_checksum_path, "w") as out_f:
        out_f.write(combined_hash)
    log_info(logger, f"Combined checksum written to {combined_checksum_path}")
