"""
Initialise reproducibility state directory.

This script creates the required JSON files for reproducibility:
- state/artifact_hashes.json
- data/checksums.json

Both files are initialised with an empty JSON object `{}` if they do not
already exist or contain invalid JSON. The script is safe to run multiple
times; it will not overwrite existing valid JSON objects.
"""

import json
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _ensure_json_file(path: str) -> None:
    """Create a JSON file at *path* containing an empty object if needed.

    If the file already exists and contains valid JSON that is a dict,
    it is left untouched. Otherwise it is overwritten with ``{}``.
    """
    file_path = path
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        try:
            content = json.loads(file_path.read_text())
            if isinstance(content, dict):
                log.debug(f"File {file_path} already contains a valid JSON object.")
                return
        except Exception as exc:
            log.warning(f"Failed to read existing JSON from {file_path}: {exc}")

    # Write empty JSON object
    file_path.write_text(json.dumps({}))
    log.info(f"Initialised empty JSON file at {file_path}")

def main() -> None:
    """Entry point for the initialisation script."""
    # Initialise artifact hashes in the state directory
    artifact_hashes_path = paths.state("artifact_hashes.json")
    _ensure_json_file(artifact_hashes_path)

    # Initialise checksums placeholder in the data directory
    checksums_path = paths.data("checksums.json")
    _ensure_json_file(checksums_path)

    log.info("Reproducibility state directory initialised successfully.")

if __name__ == "__main__":
    main()