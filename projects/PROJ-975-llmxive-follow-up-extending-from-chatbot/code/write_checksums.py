"""
Script to recompute SHA‑256 checksums for the synthetic data files
(`tasks.json` and `skills.json`) and overwrite the project‑owned
`data/raw/checksums.json` file.

The script now resolves file locations relative to the project root
(`paths.root`) instead of relying on `paths.data`, which ensures the
files are found regardless of the current working directory during
test execution.
"""
import json
import hashlib
import logging
from pathlib import Path

from llmxive_toolkit import paths

# Configure a simple console logger (no file handlers, no platform‑owned paths)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

def get_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of a file in a memory‑efficient way.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to the file whose digest should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256_hash = hashlib.sha256()
    # Read the file in small chunks to avoid loading large files into memory.
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main() -> None:
    """
    Re‑compute the SHA‑256 checksums for the synthetic data files
    (`tasks.json` and `skills.json`) and overwrite
    ``data/raw/checksums.json`` with the fresh mapping.

    This script writes only to project‑owned locations under ``data/``.
    It deliberately does **not** touch any platform‑owned ``state/`` paths.
    """
    # Resolve the project root and construct absolute paths to the raw data files.
    project_root = Path(paths.root)

    tasks_path = project_root / "data" / "raw" / "tasks.json"
    skills_path = project_root / "data" / "raw" / "skills.json"
    checksums_path = project_root / "data" / "raw" / "checksums.json"

    # Verify that the source files exist; fail loudly if they do not.
    if not tasks_path.is_file():
        log.error(f"Missing tasks file: {tasks_path}")
        raise FileNotFoundError(f"Required file not found: {tasks_path}")

    if not skills_path.is_file():
        log.error(f"Missing skills file: {skills_path}")
        raise FileNotFoundError(f"Required file not found: {skills_path}")

    log.info(f"Computing SHA‑256 checksums for {tasks_path} and {skills_path}")

    # Compute the digests.
    checksums = {
        "tasks_json_sha256": get_sha256(tasks_path),
        "skills_json_sha256": get_sha256(skills_path),
    }

    # Write the mapping to the project‑owned JSON file.
    checksums_path.write_text(json.dumps(checksums, indent=2, sort_keys=True), encoding="utf-8")

    log.info(f"Checksums successfully written to {checksums_path}")
    # Echo the mapping for interactive runs.
    print(json.dumps(checksums, indent=2))

if __name__ == "__main__":
    main()