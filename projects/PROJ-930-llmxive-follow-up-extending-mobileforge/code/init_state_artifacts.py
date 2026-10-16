"""
init_state_artifacts.py

Initialise reproducibility artefact manifests for the MobileForge Logic Distillation project.

This script creates two JSON files under the project ``data/`` directory:
  - ``artifact_hashes.json`` – an empty JSON object that will later be populated
    with SHA‑256 hashes of generated artefacts.
  - ``checksums.json`` – an empty JSON object that will be used to store
    SHA‑256 checksums of raw data files for integrity verification.

The script is deliberately lightweight and has no side‑effects outside the
``data/`` folder, respecting the platform‑owned ``state/`` directory.
"""

import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _write_empty_json(target_path: Path) -> None:
    """
    Write an empty JSON object ``{}`` to *target_path*.

    If the file already exists and contains a valid JSON mapping, it is left
    untouched; otherwise it is overwritten with an empty object.
    """
    try:
        if target_path.is_file():
            with target_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                log.debug(f"JSON manifest already present and valid: {target_path}")
                return
            else:
                log.warning(f"Existing JSON at {target_path} is not a dict – overwriting.")
    except (json.JSONDecodeError, OSError) as e:
        log.warning(f"Failed to read existing JSON at {target_path} ({e}) – overwriting.")

    # Write empty dict
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
    log.info(f"Wrote empty JSON manifest to {target_path}")

def ensure_artifact_hashes() -> None:
    """
    Ensure ``data/artifact_hashes.json`` exists and contains an empty JSON
    object. This file is used by downstream scripts to record SHA‑256 hashes
    of generated artefacts.
    """
    artifact_path = paths.data("artifact_hashes.json")
    _write_empty_json(artifact_path)

def ensure_checksums_manifest() -> None:
    """
    Ensure ``data/checksums.json`` exists and contains an empty JSON
    object. This manifest will later hold SHA‑256 checksums of raw data
    files for integrity verification.
    """
    checksum_path = paths.data("checksums.json")
    _write_empty_json(checksum_path)

def main() -> None:
    """
    Entry point used by the bootstrap process. It creates both JSON
    manifests under ``data/``.
    """
    log.info("Initialising reproducibility state manifests under data/")
    ensure_artifact_hashes()
    ensure_checksums_manifest()
    log.info("Initialisation complete.")

if __name__ == "__main__":
    main()
