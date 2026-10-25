"""
env_check.py
-------------
Verifies that the execution environment contains all required scientific
packages and that the raw data checksums are correct.
The script exits with status 0 only if every import succeeds and all
checksum validations pass.
"""
import importlib
import json
import sys
import hashlib
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# List of required packages (must be importable)
# ----------------------------------------------------------------------
REQUIRED_PACKAGES = [
    "pandas",
    "numpy",
    "sklearn",          # scikit-learn
    "torch",
    "statsmodels",
    "yaml",             # PyYAML
    "pytest",
    "jsonschema",
    "psutil",
    "openml",
    "ucimlrepo",        # now required per task T001
]

def _import_all() -> None:
    """Attempt to import every required package; raise on failure."""
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            log.debug("Successfully imported %s", pkg)
        except ImportError as exc:
            log.error("Missing required package %s: %s", pkg, exc)
            raise

# ----------------------------------------------------------------------
# Checksum utilities
# ----------------------------------------------------------------------
def _file_checksum(path: Path) -> str:
    """Return SHA‑256 checksum of the file at *path*."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _load_expected_checksums() -> dict:
    """Load the JSON mapping of expected checksums (may be empty)."""
    checksums_path = paths.raw("checksums.json")
    if not checksums_path.is_file():
        log.warning("Checksums file %s not found – treating as empty.", checksums_path)
        return {}
    with checksums_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _validate_checksums() -> None:
    """Validate that each raw file matches its recorded checksum (if any)."""
    expected = _load_expected_checksums()
    raw_dir = paths.raw()
    for file_path in raw_dir.iterdir():
        if file_path.is_file() and not file_path.name.startswith("."):
            actual = _file_checksum(file_path)
            expected_checksum = expected.get(file_path.name)
            if expected_checksum is None:
                log.info("No stored checksum for %s – skipping verification.", file_path.name)
                continue
            if actual != expected_checksum:
                raise ValueError(
                    f"Checksum mismatch for {file_path.name}: expected {expected_checksum}, got {actual}"
                )
            else:
                log.debug("Checksum verified for %s", file_path.name)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv=None) -> None:
    try:
        _import_all()
        _validate_checksums()
    except Exception as exc:
        log.error("Environment validation failed: %s", exc)
        sys.exit(1)
    log.info("All required packages are importable and raw file checksums match.")
    sys.exit(0)

if __name__ == "__main__":
    main()
