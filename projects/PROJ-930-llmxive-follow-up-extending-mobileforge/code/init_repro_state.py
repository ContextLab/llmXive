"""
init_repro_state.py

Initialise reproducibility artefacts for the MobileForge Logic Distillation project.

This script creates two JSON files:
  - ``data/checksums.json`` – an **empty** JSON object that will later be
    populated with SHA‑256 checksums of raw data files for integrity
    verification.
  - ``outputs/reproducibility_meta.json`` – a JSON object containing a
    project‑level random seed and a timestamp. The seed is taken from the
    ``RANDOM_SEED`` environment variable if present, otherwise a new
    integer seed is generated from ``random.SystemRandom``.

The script is safe to run multiple times: it overwrites
``data/checksums.json`` with an empty object (discarding any previous
content) and creates ``outputs/reproducibility_meta.json`` only if it does
not already exist, preserving reproducibility across runs.
"""

import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _write_json(target_path: Path, data: dict) -> None:
    """Write *data* as pretty‑printed JSON to *target_path*."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
    log.info(f"Wrote JSON to {target_path}")

def _ensure_empty_checksums() -> None:
    """
    Ensure ``data/checksums.json`` exists and contains an **empty** JSON
    object. Any existing content is overwritten because the reproducibility
    bootstrap requires a clean manifest.
    """
    checksum_path = paths.data("checksums.json")
    if checksum_path.is_file():
        log.debug(f"Overwriting existing checksums manifest at {checksum_path}")
    else:
        log.debug(f"Creating new checksums manifest at {checksum_path}")
    _write_json(checksum_path, {})

def _ensure_repro_meta() -> None:
    """
    Ensure ``outputs/reproducibility_meta.json`` exists with a non‑empty
    ``seed`` field and a ``timestamp`` field.

    The seed is read from the ``RANDOM_SEED`` environment variable when
    present; otherwise a cryptographically‑secure random integer is used.
    The timestamp is the current UTC time in ISO‑8601 format.
    """
    meta_path = paths.outputs("reproducibility_meta.json")
    if meta_path.is_file():
        # If the file already exists we keep it – it may have been created
        # by a previous run with the desired seed.
        log.debug(f"Reproducibility meta already exists at {meta_path}")
        return

    # Determine seed
    env_seed = os.getenv("RANDOM_SEED")
    if env_seed is not None:
        try:
            seed = int(env_seed)
            log.debug(f"Using seed from RANDOM_SEED env var: {seed}")
        except ValueError:
            log.warning(
                f"RANDOM_SEED='{env_seed}' is not a valid integer; generating a new seed."
            )
            seed = random.SystemRandom().randint(0, 2**31 - 1)
    else:
        seed = random.SystemRandom().randint(0, 2**31 - 1)
        log.debug(f"No RANDOM_SEED env var; generated seed: {seed}")

    timestamp = datetime.now(timezone.utc).isoformat()
    meta = {"seed": seed, "timestamp": timestamp}
    _write_json(meta_path, meta)

def main() -> None:
    """
    Entry point used by the bootstrap process. It creates both JSON
    manifests under their respective directories.
    """
    log.info("Initialising reproducibility artefacts...")
    _ensure_empty_checksums()
    _ensure_repro_meta()
    log.info("Initialisation complete.")

if __name__ == "__main__":
    main()
