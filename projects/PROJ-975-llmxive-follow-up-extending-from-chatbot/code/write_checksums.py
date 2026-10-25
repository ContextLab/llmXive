import json
import hashlib
from llmxive_toolkit import paths, get_logger

# Obtain a logger that integrates with the llmxive tooling.
log = get_logger(__name__)

def get_sha256(file_path):
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
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Re‑compute the SHA‑256 checksums for the synthetic data files
    (`tasks.json` and `skills.json`) and overwrite
    ``data/raw/checksums.json`` with the fresh mapping.

    This script writes only to project‑owned locations under ``data/``.
    It deliberately does **not** touch any platform‑owned ``state/`` paths.
    """
    # Resolve the expected locations of the raw data files.
    tasks_path = paths.data("raw", "tasks.json")
    skills_path = paths.data("raw", "skills.json")
    checksums_path = paths.data("raw", "checksums.json")

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
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)

    log.info(f"Checksums successfully written to {checksums_path}")
    # Echo the mapping for interactive runs (useful when script is invoked manually).
    print(json.dumps(checksums, indent=2))

if __name__ == "__main__":
    main()
