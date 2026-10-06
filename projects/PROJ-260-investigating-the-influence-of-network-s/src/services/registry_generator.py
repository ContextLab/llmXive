"""
Registry Generator Service (T055a)

Purpose:
  Generate a dataset registry mapping system sizes (N=1000, 2000, 4000)
  to valid dataset IDs sourced from the VERIFIED_DATASET_IDS constant
  defined in src/lib/config.py.

Output:
  data/metadata/dataset_registry.json
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Import from existing project API
from src.lib.config import VERIFIED_DATASET_IDS, get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_project_root() / "data" / "metadata" / "registry_generation.log")
    ]
)
logger = logging.getLogger(__name__)


def generate_registry(verified_ids: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Generate the registry mapping system sizes to dataset IDs.

    Args:
        verified_ids: The VERIFIED_DATASET_IDS constant from config.
                      Expected structure: { "N1000": [...], "N2000": [...], "N4000": [...] }

    Returns:
        A dictionary mapping system sizes to their respective dataset IDs.
    """
    logger.info("Starting registry generation from verified dataset IDs.")

    registry = {}
    required_sizes = ["N1000", "N2000", "N4000"]

    for size in required_sizes:
        if size in verified_ids and verified_ids[size]:
            registry[size] = verified_ids[size]
            logger.info(f"Found {len(verified_ids[size])} dataset(s) for size {size}.")
        else:
            # If missing, we still record it as an empty list to be caught by T055b
            registry[size] = []
            logger.warning(f"No dataset IDs found for size {size} in verified sources.")

    if not any(registry.values()):
        logger.error("Registry generation failed: No dataset IDs found for any required system size.")
        raise ValueError("Registry generation failed: No valid dataset IDs found.")

    logger.info("Registry generation completed successfully.")
    return registry


def write_registry(registry: Dict[str, List[str]], output_path: Path) -> None:
    """
    Write the generated registry to a JSON file.

    Args:
        registry: The registry dictionary to write.
        output_path: The path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2)

    logger.info(f"Registry written to {output_path}")


def main() -> int:
    """
    Main entry point for the registry generator.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        project_root = get_project_root()
        output_path = project_root / "data" / "metadata" / "dataset_registry.json"

        logger.info(f"Project root identified: {project_root}")
        logger.info(f"Using verified dataset IDs from config.")

        # Generate registry
        registry = generate_registry(VERIFIED_DATASET_IDS)

        # Write registry
        write_registry(registry, output_path)

        logger.info("T055a completed successfully.")
        return 0

    except Exception as e:
        logger.critical(f"T055a failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
