"""
init_state_artifacts.py

This script initialises the reproducibility artefact manifests required by the
MobileForge Logic Distillation project.  It creates two JSON files under the
project‑owned ``data/`` directory:

* ``data/artifact_hashes.json`` – an empty mapping that will later be populated
  with SHA‑256 hashes of generated artefacts.
* ``data/checksums.json`` – an empty mapping used to store checksums of raw
  input files.

The script follows the same contract as the original ``init_state_artifacts``
implementation but avoids writing to the platform‑owned ``state/`` directory,
which is managed by the verification infrastructure.  Running the script is
idempotent: if a target file already exists and contains a valid JSON object,
it is left untouched; otherwise it is overwritten with ``{}``.

The script can be invoked directly:

    python code/init_state_artifacts.py

It will log its actions via the shared ``llmxive_toolkit`` logger.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _write_empty_json(target_path: Path) -> None:
    """
    Write an empty JSON object ``{}`` to *target_path* if the file does not
    already exist or does not contain a valid JSON mapping.

    Parameters
    ----------
    target_path: Path
        The path of the JSON file to initialise.
    """
    if target_path.exists():
        try:
            content = json.loads(target_path.read_text())
            if isinstance(content, dict):
                log.info(f"{target_path} already contains a valid JSON object.")
                return
        except Exception as exc:
            log.warning(f"Failed to parse existing JSON at {target_path}: {exc}")

    # Write a fresh empty JSON object
    target_path.write_text("{}\n")
    log.info(f"Wrote empty JSON object to {target_path}")

def ensure_artifact_hashes() -> None:
    """
    Ensure ``data/artifact_hashes.json`` exists and contains an empty object.
    """
    artifact_path = paths.data("artifact_hashes.json")
    _write_empty_json(artifact_path)

def ensure_checksums_manifest() -> None:
    """
    Ensure ``data/checksums.json`` exists and contains an empty object.
    """
    checksums_path = paths.data("checksums.json")
    _write_empty_json(checksums_path)

def main() -> None:
    """
    Entry point for the initialisation script.  It creates the two JSON
    manifest files under ``data/``.
    """
    ensure_artifact_hashes()
    ensure_checksums_manifest()

if __name__ == "__main__":
    main()