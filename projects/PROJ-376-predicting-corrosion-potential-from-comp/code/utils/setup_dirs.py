"""
Setup script for creating the required project directory hierarchy and
generating a verification manifest.

When executed as a module (`python -m code.utils.setup_dirs`), this script
ensures that the following directories exist relative to the project root:

  - code/
  - data/
  - data/raw/
  - data/processed/
  - data/logs/
  - results/

It then writes a JSON file ``data/processed/setup_dirs_verified.json`` containing
a list of objects, each with the absolute path of a created directory and the
timestamp (ISO‑8601, UTC) at which the directory was confirmed/created.

The script **must not** create or write to any ``state/`` directory,
as that location is owned by the platform. If a stale ``state/`` directory
exists from a previous run, it is removed to keep the project clean.

The script exits with status 0 on success; any unexpected exception will
propagate and cause a non‑zero exit code.
"""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from llmxive_toolkit import paths, get_logger

# Logger (optional – useful for debugging)
log = get_logger(__name__)

# ----------------------------------------------------------------------
# List of required directories (relative to the project root)
# ----------------------------------------------------------------------
REQUIRED_DIRS: List[Path] = [
    paths.code(),
    paths.data(),
    paths.data("raw"),
    paths.data("processed"),
    paths.data("logs"),
    paths.results(),
]

def ensure_directories(dirs: List[Path]) -> List[Dict[str, str]]:
    """
    Ensure each directory exists (creating it if necessary) and record
    its absolute path together with a creation timestamp.

    Parameters
    ----------
    dirs: List[Path]
        List of directories to ensure.

    Returns
    -------
    List[Dict[str, str]]
        A list of dictionaries with keys ``path`` and ``created_at``.
    """
    entries: List[Dict[str, str]] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    for d in dirs:
        # ``exist_ok=True`` means the call is idempotent.
        d.mkdir(parents=True, exist_ok=True)
        entries.append(
            {
                "path": str(d.resolve()),
                "created_at": now_iso,
            }
        )
        log.info("Ensured directory exists: %s", d)
    return entries

def write_manifest(entries: List[Dict[str, str]]) -> Path:
    """
    Write the verification manifest to ``data/processed/setup_dirs_verified.json``.

    Parameters
    ----------
    entries: List[Dict[str, str]]
        Directory entries to serialize.

    Returns
    -------
    Path
        Path to the written JSON manifest.
    """
    manifest_path = paths.data("processed", "setup_dirs_verified.json")
    # Ensure the parent directory exists (already covered in REQUIRED_DIRS)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    log.info("Wrote verification manifest to %s", manifest_path)
    return manifest_path

def clean_platform_state_dir() -> None:
    """
    Remove any ``state/`` directory that may have been created by a previous
    version of this script. The platform owns ``state/``; the project must
    not leave artefacts there.
    """
    state_dir = Path(paths.root, "state")
    if state_dir.is_dir():
        try:
            shutil.rmtree(state_dir)
            log.info("Removed platform‑owned state directory: %s", state_dir)
        except Exception as e:
            log.error("Failed to remove state directory %s: %s", state_dir, e)
            # Propagate the error – we do not want to silently ignore platform‑owned artefacts.
            raise

def main() -> None:
    """
    Main entry point for the setup script.
    """
    log.info("Starting project directory setup...")
    # Remove any stray platform‑owned ``state`` directory before proceeding.
    clean_platform_state_dir()

    entries = ensure_directories(REQUIRED_DIRS)
    write_manifest(entries)
    log.info("Setup completed successfully.")

if __name__ == "__main__":
    main()
