"""
Setup script for creating required data directory structure and initializing
essential files such as the exclusion log. This script is idempotent – it can be
run multiple times without overwriting existing data.
"""
import json
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def ensure_data_directories() -> None:
    """
    Create the data sub‑directories required by the pipeline:
    - data/raw
    - data/derived
    - data/logs
    The function uses the llmxive_toolkit `paths` helper which creates parent
    directories as needed.
    """
    raw_dir = paths.data("raw")
    derived_dir = paths.data("derived")
    logs_dir = paths.data("logs")

    # The `paths` helpers already ensure the parent directories exist.
    raw_dir.mkdir(parents=True, exist_ok=True)
    derived_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"Ensured data directories: {raw_dir}, {derived_dir}, {logs_dir}")

def initialise_exclusion_log() -> None:
    """
    Create an empty exclusion log JSON file at
    `data/logs/exclusion_log.json` if it does not already exist.
    The log is a JSON list where each entry records a subject exclusion
    event (subject_id, reason, timestamp). Starting with an empty list
    satisfies downstream scripts that expect the file to be present.
    """
    exclusion_log_path = paths.path("data", "logs", "exclusion_log.json")
    if not exclusion_log_path.exists():
        exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
        with exclusion_log_path.open("w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        log.info(f"Created empty exclusion log at {exclusion_log_path}")
    else:
        log.info(f"Exclusion log already exists at {exclusion_log_path}")

def main() -> None:
    """Entry point executed when the script is run."""
    log.info("Running data‑structure setup script...")
    ensure_data_directories()
    initialise_exclusion_log()
    log.info("Data‑structure setup completed successfully.")

if __name__ == "__main__":
    main()
