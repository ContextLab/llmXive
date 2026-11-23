"""
Registry Generator Service (T055a)

Purpose:
Generate a JSON registry mapping system sizes (N=1000, 2000, 4000) to valid
dataset IDs from verified sources (e.g., Zenodo, Materials Cloud) by querying
the VERIFIED_DATASET_IDS constant in src/lib/config.py.

Output:
data/metadata/dataset_registry.json
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lib.config import VERIFIED_DATASET_IDS, get_project_root

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_project_root() / "data" / "metadata" / "registry_generator.log")
    ]
)
logger = logging.getLogger(__name__)


def generate_registry() -> dict:
    """
    Generate the dataset registry by mapping system sizes to dataset IDs.

    Returns:
        dict: A dictionary mapping system sizes (N) to lists of dataset IDs.
    """
    if not VERIFIED_DATASET_IDS:
        logger.error("VERIFIED_DATASET_IDS is empty in config. Cannot generate registry.")
        raise ValueError("No verified dataset IDs found in configuration.")

    # Expected system sizes based on the project plan
    expected_sizes = [1000, 2000, 4000]

    registry = {}

    # Group dataset IDs by system size
    # The VERIFIED_DATASET_IDS constant should be a dict or list of dicts with 'size' and 'id' keys
    # Assuming structure: [{'id': 'zenodo_123', 'size': 1000}, ...]
    if isinstance(VERIFIED_DATASET_IDS, dict):
        # If it's a flat dict, assume keys are IDs and values are sizes or metadata
        # We need to adapt based on actual config structure.
        # For robustness, let's assume it's a list of dicts as per common patterns.
        # If it's a dict, we might need to iterate differently.
        # Let's handle the most likely case: a list of dicts.
        logger.warning("VERIFIED_DATASET_IDS is a dict, but expected a list of dicts. Attempting to adapt.")
        # Fallback: if it's a dict, maybe it's {id: size}
        items = [{"id": k, "size": v} for k, v in VERIFIED_DATASET_IDS.items()]
    elif isinstance(VERIFIED_DATASET_IDS, list):
        items = VERIFIED_DATASET_IDS
    else:
        raise TypeError(f"Unexpected type for VERIFIED_DATASET_IDS: {type(VERIFIED_DATASET_IDS)}")

    for item in items:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in VERIFIED_DATASET_IDS: {item}")
            continue

        dataset_id = item.get("id")
        size = item.get("size")

        if not dataset_id or size is None:
            logger.warning(f"Skipping item missing 'id' or 'size': {item}")
            continue

        if size in expected_sizes:
            if size not in registry:
                registry[size] = []
            registry[size].append(dataset_id)
            logger.info(f"Registered dataset ID '{dataset_id}' for size {size}")
        else:
            logger.debug(f"Ignoring dataset ID '{dataset_id}' for unsupported size {size}")

    # Validate that all expected sizes are present
    missing_sizes = [s for s in expected_sizes if s not in registry]
    if missing_sizes:
        logger.warning(f"Missing dataset IDs for system sizes: {missing_sizes}")
        # We do not raise here, as the downstream task (T055b/T056) will handle validation
        # and halt if critical data is missing.

    return registry


def write_registry(registry: dict, output_path: Path) -> None:
    """
    Write the registry dictionary to a JSON file.

    Args:
        registry: The registry dictionary.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
    logger.info(f"Registry written to {output_path}")


def main() -> int:
    """
    Main entry point for the registry generator.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        logger.info("Starting registry generation...")
        registry = generate_registry()
        output_path = get_project_root() / "data" / "metadata" / "dataset_registry.json"
        write_registry(registry, output_path)
        logger.info("Registry generation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Registry generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
