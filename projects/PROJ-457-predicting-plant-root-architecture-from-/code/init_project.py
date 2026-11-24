"""
init_project.py
----------------
Script to initialize the project directory structure and basic logging.
This fulfills task T001: create the required top‑level folders
(`code/`, `tests/`, `data/raw`, `data/processed`, `artifacts/`, `logs/`)
and set up a logger for the pipeline.
The script is idempotent: it can be run multiple times without error.
"""

import logging
from llmxive_toolkit import paths, get_logger
from config import setup_logging


def _create_directories() -> None:
    """
    Create the required project directories if they do not already exist.
    """
    # Define the directories to ensure exist
    required_dirs = [
        paths.code(),
        paths.tests(),
        paths.data("raw"),
        paths.data("processed"),
        paths.artifacts(),
        paths.logs(),
    ]

    for d in required_dirs:
        # `mkdir` with `parents=True` creates any missing parent directories.
        # `exist_ok=True` makes the operation safe to repeat.
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Entry point for the init script.
    """
    # Initialise logging as defined in the project's config module.
    # This will configure a file logger under the `logs/` directory
    # and also emit to the console.
    try:
        setup_logging()
    except Exception as exc:
        # If configuration fails we still want the script to continue;
        # fall back to a basic configuration so that we can log the
        # directory‑creation steps.
        logging.basicConfig(level=logging.INFO)
        get_logger(__name__).warning(
            "Failed to run project config.setup_logging(): %s. "
            "Falling back to basic logging configuration.",
            exc,
        )

    logger = get_logger(__name__)  # Project‑wide logger

    logger.info("Starting project directory initialization.")

    _create_directories()

    logger.info(
        "Created/verified required directories: %s",
        ", ".join(
            str(d)
            for d in [
                paths.code(),
                paths.tests(),
                paths.data("raw"),
                paths.data("processed"),
                paths.artifacts(),
                paths.logs(),
            ]
        ),
    )

    logger.info("Project initialization complete.")


if __name__ == "__main__":
    main()
