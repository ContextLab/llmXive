"""Setup logging infrastructure for the project.

This script ensures that the logging system is initialized so that
logs are written to both the console and the YAML file
``data/preprocessing.yaml`` as required by task T009.

It can be safely re‑run; the logger will be re‑initialized and the
YAML file will be created if it does not already exist.
"""

import logging
from pathlib import Path

# Import the project's logging utilities
from logging_config import initialize_logging, log_step

def main() -> None:
    """Initialize logging and create the YAML log file."""
    # Ensure the ``data`` directory exists
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialise the logger – this creates ``data/preprocessing.log``
    # and ``data/preprocessing.yaml`` (if they do not already exist)
    logger = initialize_logging()

    # Record a simple step indicating that logging has been set up
    log_step("logging_initialized", {"status": "success"})

    # Ensure the YAML file exists; ``initialize_logging`` should have
    # created it, but we add a minimal structure as a safety net.
    yaml_path = data_dir / "preprocessing.yaml"
    if not yaml_path.exists():
        yaml_path.write_text("log: []\n")

    logger.info("Logging infrastructure is ready (console + YAML).")

if __name__ == "__main__":
    main()