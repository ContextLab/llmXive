"""
Registry Generator Service (T008)

Purpose:
  Generate a dataset registry mapping system sizes (N1000, N2000, N4000)
  to verified dataset IDs sourced from the VERIFIED_DATASET_IDS constant
  defined in src/lib/config.py.

Output:
  data/metadata/dataset_registry.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List

# Import from existing project API
from src.lib.config import VERIFIED_DATASET_IDS, get_project_root

# -------------------------------------------------------------------------
# Logger configuration
# -------------------------------------------------------------------------
def _get_logger() -> logging.Logger:
    """
    Create (or retrieve) a logger for the registry generator.

    The logger is configured lazily to avoid side‑effects at import time.
    A file handler is added only when the logger is first used, and the
    target directory is created if it does not yet exist.
    """
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(module)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler – ensure the parent directory exists
        log_path = get_project_root() / "data" / "metadata" / "registry_generation.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)

    return logger

logger = _get_logger()

# -------------------------------------------------------------------------
# Core functionality
# -------------------------------------------------------------------------
def generate_registry(verified_ids: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Generate the registry mapping system sizes to dataset IDs.

    Args:
        verified_ids: Mapping from size label (e.g., "N1000") to a list of
                      dataset identifiers.

    Returns:
        A dictionary with keys "N1000", "N2000", "N4000". Missing sizes are
        represented by empty lists.
    """
    logger.info("Starting registry generation from verified dataset IDs.")

    registry: Dict[str, List[str]] = {}
    required_sizes = ["N1000", "N2000", "N4000"]

    for size in required_sizes:
        ids = verified_ids.get(size, [])
        if ids:
            logger.info(f"Found {len(ids)} dataset(s) for size {size}.")
        else:
            logger.warning(f"No dataset IDs found for size {size}.")
        registry[size] = ids

    # If *all* entries are empty, raise an error – the pipeline cannot proceed.
    if not any(registry.values()):
        logger.error("Registry generation failed: No dataset IDs found for any required system size.")
        raise ValueError("Registry generation failed: No valid dataset IDs found.")

    logger.info("Registry generation completed successfully.")
    return registry


def write_registry(registry: Dict[str, List[str]], output_path: Path) -> None:
    """
    Write the generated registry to a JSON file.

    Args:
        registry: The registry dictionary to serialize.
        output_path: Destination file path (including filename).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Registry written to {output_path}")


def main() -> int:
    """
    Entry point for the registry generator CLI.

    Returns:
        0 on success, 1 on any failure.
    """
    try:
        project_root = get_project_root()
        output_path = project_root / "data" / "metadata" / "dataset_registry.json"

        logger.info(f"Project root identified: {project_root}")

        # Generate and write the registry
        registry = generate_registry(VERIFIED_DATASET_IDS)
        write_registry(registry, output_path)

        logger.info("T008 (registry_generator) completed successfully.")
        return 0

    except Exception as exc:  # pragma: no cover – exercised via tests / CLI
        logger.critical(f"T008 failed with error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())