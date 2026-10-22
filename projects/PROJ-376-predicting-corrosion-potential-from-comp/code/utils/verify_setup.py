"""
verify_setup.py
----------------
This script verifies that the directory setup performed by `setup_dirs.py`
was successful. It reads the manifest file
`state/setup_dirs_verified.json`, checks that all required directories are
listed, and confirms that each directory actually exists on the filesystem.

Exit Codes
----------
* Exit with status 0 (i.e., no exception) when **all** required directories
  are present in the manifest and exist on disk.
* Raise a `RuntimeError` with a descriptive message if any directory is
  missing from the manifest or does not exist.

The script is intended to be run via:
    python -m code.utils.verify_setup
"""

import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# List of directories that `setup_dirs.py` must have created.
REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/logs",
    "results",
    "state",
]

def _load_manifest(manifest_path: Path) -> list[dict]:
    """Load the JSON manifest produced by ``setup_dirs.py``."""
    if not manifest_path.is_file():
        raise RuntimeError(f"Setup manifest not found at '{manifest_path}'.")
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse manifest JSON: {exc}") from exc

    if not isinstance(data, list):
        raise RuntimeError("Setup manifest JSON must be a list of entries.")
    return data

def _build_required_paths() -> dict[str, Path]:
    """Map required relative directory strings to their absolute Path objects."""
    root = paths.root
    return {rel: root / rel for rel in REQUIRED_DIRS}

def _verify_entries(manifest: list[dict], required_paths: dict[str, Path]) -> None:
    """Ensure every required directory appears in the manifest and exists."""
    # Build a set of absolute paths present in the manifest for fast lookup.
    manifest_paths = {Path(entry.get("path", "")) for entry in manifest}
    missing = []
    for rel, abs_path in required_paths.items():
        if abs_path not in manifest_paths:
            missing.append(f"Missing manifest entry for '{abs_path}'.")
        elif not abs_path.is_dir():
            missing.append(f"Directory does not exist on disk: '{abs_path}'.")
    if missing:
        error_msg = "Setup verification failed:\\n" + "\\n".join(missing)
        raise RuntimeError(error_msg)

def main() -> None:
    """Entry point for the verification script."""
    manifest_path = paths.state("setup_dirs_verified.json")
    log.info("Loading setup manifest from %s", manifest_path)
    manifest = _load_manifest(manifest_path)

    required_paths = _build_required_paths()
    log.debug("Required directories: %s", required_paths)

    _verify_entries(manifest, required_paths)
    log.info("All required directories are present and verified.")

if __name__ == "__main__":
    main()
