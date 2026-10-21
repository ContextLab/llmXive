"""
verify_requirements.py

This script verifies that a pinned ``requirements.txt`` file exists at the repository
root, is non‑empty, and (optionally) matches the SHA‑256 hash recorded in
``data/artifact_hashes.yaml``.  It writes a concise log to
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

def check_requirements() -> bool:
    """
    Perform the verification steps.

    Returns
    -------
    bool
        ``True`` if all checks pass, ``False`` otherwise.
    """
    repo_root = paths.root
    req_path = repo_root / "requirements.txt"
    log_path = paths.data("requirements_check.log")

    # Ensure the log file exists (it will be overwritten each run)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_log(message: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        line = f"[{timestamp}] {message}"
        log_path.write_text(line + "\n", encoding="utf-8")
        log.info(message)

    # 1. Existence
    if not req_path.is_file():
        _write_log("FAILURE: requirements.txt not found at repository root.")
        return False

    # 2. Non‑empty
    if req_path.stat().st_size == 0:
        _write_log("FAILURE: requirements.txt is empty.")
        return False

    _write_log("PASS: requirements.txt exists and is non‑empty.")

    # 3. Optional SHA‑256 verification
    manifest = _load_hash_manifest()
    expected_hash = manifest.get("requirements.txt")
    if expected_hash:
        actual_hash = _sha256(req_path)
        if actual_hash.lower() != expected_hash.lower():
            _write_log(
                f"FAILURE: SHA‑256 mismatch for requirements.txt. "
                f"expected={expected_hash}, actual={actual_hash}"
            )
            return False
        _write_log("PASS: SHA‑256 hash of requirements.txt matches manifest.")
    else:
        _write_log(
            "NOTE: No SHA‑256 entry for requirements.txt in data/artifact_hashes.yaml; "
            "hash verification skipped."
        )

    # All checks passed
    _write_log("SUCCESS: requirements.txt verification completed.")
    return True

def main() -> None:
    """Entry‑point for ``python -m src.utils.verify_requirements``."""
    success = check_requirements()
    # Exit code reflects the boolean flag
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
