"""
Verification script for the directory‑setup manifest produced by
``code.utils.setup_dirs`` (T001a).

The script reads ``state/setup_dirs_verified.json`` and checks that
every required directory (code, data, data/raw, data/processed, data/logs,
results) is present in the manifest. If any entry is missing, a
``RuntimeError`` is raised; otherwise the script exits with status 0.
"""
import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Required directories that should be listed in the manifest.
REQUIRED_DIRS = {
    str(paths.code().resolve()),
    str(paths.data().resolve()),
    str(paths.data("raw").resolve()),
    str(paths.data("processed").resolve()),
    str(paths.data("logs").resolve()),
    str(paths.results().resolve()),
}

# The manifest is stored in the platform‑owned ``state`` directory.
# Reading from this location is allowed; the script does not write there.
MANIFEST_PATH = paths.state("setup_dirs_verified.json")

def load_manifest() -> list[dict]:
    """Load the JSON manifest containing directory creation records.

    Returns
    -------
    list[dict]
        List of manifest entries, each with at least a ``"path"`` key.
    """
    if not MANIFEST_PATH.is_file():
        raise RuntimeError(f"Manifest file not found: {MANIFEST_PATH}")
    with MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def verify() -> None:
    """Verify that every required directory appears in the manifest."""
    entries = load_manifest()
    manifest_paths = {entry["path"] for entry in entries}
    missing = REQUIRED_DIRS - manifest_paths
    if missing:
        raise RuntimeError(
            f"Missing required directories in manifest: {missing}"
        )
    log.info("All required directories verified in manifest.")

def main() -> None:
    """Entry point for command‑line execution."""
    verify()
    log.info("Directory‑setup verification succeeded.")

if __name__ == "__main__":
    main()