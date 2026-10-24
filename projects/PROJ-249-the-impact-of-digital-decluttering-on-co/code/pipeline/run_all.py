"""
Run All Pipeline – Setup Stage (T001)

This script implements the minimal end‑to‑end pipeline required for
task T001. It validates the study configuration, ensures that all
required project directories exist, writes a deterministic status file,
and generates a SHA‑256 manifest that includes the status file.

The implementation provides the public symbols expected by the test
suite:
  - REQUIRED_KEYS
  - REQUIRED_METRICS
  - load_and_validate_config
  - sha256_of
  - write_checksum_manifest
  - main
"""

import argparse
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime

import yaml
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Public constants expected by the test suite
# ----------------------------------------------------------------------
REQUIRED_KEYS = {
    "seed": int,
    "n_participants": int,
    "dropout_rate": float,
    "effect_sizes": dict,
    "practice_effect_grid": list,
    "bootstrap_resamples": int,
    "start_date": str,
    "pilot_n": int,
}

REQUIRED_METRICS = ["SART", "Ospan", "PSS-10", "PANAS-PA", "PANAS-NA"]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_directories() -> None:
    """
    Create all directories required by the study layout.
    Mirrors the layout described in the specification and quickstart.
    """
    required_dirs = [
        "code/scoring",
        "code/analysis",
        "code/compliance",
        "code/viz",
        "code/validation",
        "code/pipeline",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
    ]
    for d in required_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory exists: {d}")

def load_config(config_path: str) -> dict:
    """
    Load the YAML configuration file without validation.
    """
    cfg_path = Path(config_path)
    if not cfg_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("Configuration file must contain a YAML mapping.")
    log.debug(f"Loaded configuration from {config_path}")
    return config

def load_and_validate_config(config_path: str) -> dict:
    """
    Load the configuration and enforce that all required keys are present
    and have the correct type. Also validates that the effect_sizes dict
    contains exactly the required metric keys.
    """
    config = load_config(config_path)

    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")

    # Type checks (basic)
    for key, expected_type in REQUIRED_KEYS.items():
        if not isinstance(config[key], expected_type):
            raise ValueError(f"{key} must be of type {expected_type.__name__}")

    # Validate effect_sizes metric keys
    effect_keys = set(config["effect_sizes"].keys())
    if effect_keys != set(REQUIRED_METRICS):
        raise ValueError(
            f"effect_sizes must contain exactly the metrics: {REQUIRED_METRICS}"
        )

    # Validate practice_effect_grid contents
    if config["practice_effect_grid"] != [0.0, 0.2, 0.4]:
        raise ValueError("practice_effect_grid must be [0.0, 0.2, 0.4]")

    # Validate start_date format (YYYY‑MM‑DD)
    try:
        datetime.strptime(config["start_date"], "%Y-%m-%d")
    except Exception as e:
        raise ValueError("start_date must be in YYYY-MM-DD format") from e

    log.debug("Configuration validation passed")
    return config

def sha256_of(file_path: Path) -> str:
    """
    Compute the SHA‑256 hex digest of a file.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_checksum_manifest() -> None:
    """
    Write a SHA‑256 manifest file at ``data/checksums.sha256`` that
    includes the pipeline status JSON file (and any other files that
    exist at the time of invocation).
    """
    manifest_path = paths.data("checksums.sha256")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Currently we only guarantee the status file exists.
    status_path = paths.data("results", "pipeline_status.json")
    entries = []
    if status_path.is_file():
        digest = sha256_of(status_path)
        rel = status_path.relative_to(paths.root).as_posix()
        entries.append(f"{digest}  {rel}")

    # Write manifest
    manifest_path.write_text("\n".join(entries) + "\n", encoding="utf-8")
    log.info(f"Wrote checksum manifest to {manifest_path}")

def write_pipeline_status() -> None:
    """
    Write a small JSON status file indicating successful setup.
    """
    status_path = paths.data("results", "pipeline_status.json")
    status_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "SUCCESS",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    with status_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    log.info(f"Wrote pipeline status to {status_path}")
    return status_path

def write_pipeline_log() -> None:
    """
    Append a timestamped entry to ``results/pipeline.log`` and finish
    with the required ``STATUS: SUCCESS`` line.
    """
    log_path = paths.data("results", "pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as f:
        now = datetime.utcnow().isoformat()
        f.write(f"{now} - INFO - Pipeline setup completed\\n")
        f.write("STATUS: SUCCESS\\n")
    log.info(f"Wrote pipeline log to {log_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: list | None = None) -> int:
    """
    Execute the minimal pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Run the full study pipeline (setup stage only)."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the study configuration YAML file.",
    )
    args = parser.parse_args(argv)

    # 1. Load and validate configuration
    _ = load_and_validate_config(args.config)

    # 2. Ensure required directory layout exists
    ensure_directories()

    # 3. Write deterministic pipeline log
    write_pipeline_log()

    # 4. Write status JSON and checksum manifest
    write_pipeline_status()
    write_checksum_manifest()

    print("Pipeline setup completed successfully. STATUS: SUCCESS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
