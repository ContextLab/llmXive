"""
verify_setup.py
----------------
This script verifies that the directory setup performed by `setup_dirs.py`
was successful. It reads the manifest file that records the created
directories and checks that all required directories are listed and
actually exist on disk.

The original implementation stored the manifest under the platform‑owned
`state/` directory, which is prohibited. The updated script now stores
and reads the manifest under a project‑owned location:
    data/state/setup_dirs_verified.json

If the manifest is still present only under the old `state/` path (e.g.,
from a previous run), the script will copy it to the new location so
downstream tasks can rely on the correct path.

Exit Codes
----------
* Exit with status 0 when **all** required directories are present in the
  manifest and exist on disk.
* Raise a `RuntimeError` with a descriptive message if any directory is
  missing from the manifest or does not exist.

The script is intended to be run via:
    python -m code.utils.verify_setup
"""

import json
import shutil
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

# New, project‑owned location for the manifest.
NEW_MANIFEST_PATH = paths.data("state", "setup_dirs_verified.json")
# Legacy, platform‑owned location (kept for backward compatibility).
LEGACY_MANIFEST_PATH = paths.state("setup_dirs_verified.json")


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


def _ensure_new_manifest() -> Path:
    """
    Ensure the manifest exists at the new project‑owned location.
    If it only exists under the legacy path, copy it over.
    Returns the path of the manifest that will be used for verification.
    """
    if NEW_MANIFEST_PATH.is_file():
        return NEW_MANIFEST_PATH

    # Fallback to the legacy location.
    if LEGACY_MANIFEST_PATH.is_file():
        # Ensure the target directory exists.
        NEW_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LEGACY_MANIFEST_PATH, NEW_MANIFEST_PATH)
        log.info(
            "Copied legacy manifest from %s to project‑owned location %s",
            LEGACY_MANIFEST_PATH,
            NEW_MANIFEST_PATH,
        )
        return NEW_MANIFEST_PATH

    # Neither manifest exists – raise an informative error.
    raise RuntimeError(
        f"Setup manifest not found. Expected either {NEW_MANIFEST_PATH} "
        f"or legacy location {LEGACY_MANIFEST_PATH}."
    )


def main() -> None:
    """Entry point for the verification script."""
    manifest_path = _ensure_new_manifest()
    log.info("Loading setup manifest from %s", manifest_path)
    manifest = _load_manifest(manifest_path)

    required_paths = _build_required_paths()
    log.debug("Required directories: %s", required_paths)

    _verify_entries(manifest, required_paths)
    log.info("All required directories are present and verified.")


if __name__ == "__main__":
    main()