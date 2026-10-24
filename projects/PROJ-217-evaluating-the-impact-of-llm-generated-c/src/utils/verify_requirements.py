"""
verify_requirements.py

This script verifies that a pinned ``requirements.txt`` file exists within the
``code/`` directory of the repository, is non‑empty, and (optionally) matches the
SHA‑256 hash recorded in ``data/artifact_hashes.yaml``.  It writes a concise log to
``data/requirements_check.log`` and exits with a non‑zero status if any check fails.

The script is intended to be run as a module:

    python -m src.utils.verify_requirements

It can also be imported and the ``check_requirements`` function called directly.
"""

import hashlib
import sys
from datetime import datetime
from pathlib import Path

import yaml

from llmxive_toolkit import paths, get_logger

# Initialise a logger – it will also write to the same log file we create manually.
log = get_logger(__name__)

def _sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_hash_manifest() -> dict:
    """Load ``data/artifact_hashes.yaml`` if it exists, otherwise return an empty dict."""
    manifest_path = paths.data("artifact_hashes.yaml")
    if not manifest_path.is_file():
        return {}
    with manifest_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _append_log(log_path: Path, message: str) -> None:
    """Append a timestamped message to the log file."""
    timestamp = datetime.utcnow().isoformat()
    line = f"[{timestamp}] {message}"
    # Ensure the parent directory exists (paths.data already creates it, but be safe)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    log.info(message)

def check_requirements() -> bool:
    """
    Perform the verification steps.

    Returns
    -------
    bool
        ``True`` if all checks pass, ``False`` otherwise.
    """
    repo_root = paths.root
    # The requirements file must reside under the ``code`` subdirectory.
    req_path = repo_root / "code" / "requirements.txt"
    log_path = paths.data("requirements_check.log")

    # Start with a fresh log file for this run
    if log_path.is_file():
        log_path.unlink()
    _append_log(log_path, "START: requirements verification")

    # 1. Existence
    if not req_path.is_file():
        _append_log(
            log_path,
            f"FAILURE: requirements.txt not found at expected location: {req_path}"
        )
        return False

    # 2. Non‑empty
    if req_path.stat().st_size == 0:
        _append_log(log_path, "FAILURE: requirements.txt is empty.")
        return False

    _append_log(log_path, "PASS: requirements.txt exists and is non‑empty.")

    # 3. Optional SHA‑256 verification
    manifest = _load_hash_manifest()
    expected_hash = manifest.get("requirements.txt")
    if expected_hash:
        actual_hash = _sha256(req_path)
        if actual_hash.lower() != expected_hash.lower():
            _append_log(
                log_path,
                f"FAILURE: SHA‑256 mismatch for requirements.txt. "
                f"expected={expected_hash}, actual={actual_hash}"
            )
            return False
        _append_log(log_path, "PASS: SHA‑256 hash of requirements.txt matches manifest.")
    else:
        _append_log(
            log_path,
            "NOTE: No SHA‑256 entry for requirements.txt in data/artifact_hashes.yaml; "
            "hash verification skipped."
        )

    # All checks passed
    _append_log(log_path, "SUCCESS: requirements.txt verification completed.")
    return True

def main() -> None:
    """Entry‑point for ``python -m src.utils.verify_requirements``."""
    success = check_requirements()
    # Exit code reflects the boolean flag
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()