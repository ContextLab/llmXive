import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Import from local project structure
try:
    from src.lib.config import get_project_root, get_config
except Exception:  # pragma: no cover
    # Fallback for environments where config utilities are unavailable.
    def get_project_root() -> Path:
        """Return the repository root (assumed two levels up from this file)."""
        return Path(__file__).resolve().parents[2]

    def get_config(*args, **kwargs):
        return {}

# ----------------------------------------------------------------------
# Logger setup
# ----------------------------------------------------------------------
def setup_logger(name: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if logger is re-used
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler (INFO level)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler (DEBUG level)
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# ----------------------------------------------------------------------
# Registry handling
# ----------------------------------------------------------------------
def load_registry(registry_path: Path) -> Dict[str, Any]:
    """Load the dataset registry JSON."""
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------
def validate_dataset_id(dataset_id: str, logger: logging.Logger) -> bool:
    """
    Validate a dataset ID by checking its reachability.
    Supports Zenodo numeric IDs and HuggingFace dataset identifiers.
    """
    # Heuristic: numeric IDs are Zenodo, otherwise assume HuggingFace
    is_zenodo = dataset_id.isdigit() or "zenodo" in dataset_id.lower()

    if is_zenodo:
        return validate_zenodo_id(dataset_id, logger)
    else:
        return validate_hf_id(dataset_id, logger)

def validate_zenodo_id(dataset_id: str, logger: logging.Logger) -> bool:
    """Validate a Zenodo dataset ID via the public Zenodo API."""
    import requests

    url = f"https://zenodo.org/api/records/{dataset_id}"
    try:
        logger.debug(f"Checking Zenodo ID {dataset_id} at {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "metadata" in data:
                logger.info(f"Zenodo ID {dataset_id} is valid.")
                return True
            logger.warning(f"Zenodo ID {dataset_id} returned 200 but lacks metadata.")
            return False
        logger.warning(
            f"Zenodo ID {dataset_id} returned unexpected status {response.status_code}"
        )
        return False
    except requests.RequestException as e:
        logger.error(f"Network error checking Zenodo ID {dataset_id}: {e}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response for Zenodo ID {dataset_id}")
        return False

def validate_hf_id(dataset_id: str, logger: logging.Logger) -> bool:
    """Validate a HuggingFace dataset ID using the `datasets` library."""
    try:
        from datasets import get_dataset_config_names

        logger.debug(f"Checking HuggingFace dataset {dataset_id}")
        try:
            configs = get_dataset_config_names(dataset_id)
            logger.info(f"HuggingFace dataset {dataset_id} is valid. Configs: {configs}")
            return True
        except Exception as e:
            logger.warning(f"HuggingFace dataset {dataset_id} validation failed: {e}")
            return False
    except ImportError:
        logger.error(
            "The 'datasets' library is required for HuggingFace validation but is not installed."
        )
        return False
    except Exception as e:
        logger.error(f"Unexpected error during HF validation for {dataset_id}: {e}")
        return False

def validate_registry(registry: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate all dataset IDs in the supplied registry.
    Returns a dict with lists of valid and invalid IDs and an overall status flag.
    """
    valid_ids: List[str] = []
    invalid_ids: List[str] = []

    for size, entries in registry.items():
        logger.info(f"Validating entries for system size {size}")

        # Normalise the entry format to a flat list of IDs
        if isinstance(entries, list):
            ids_to_check = entries
        elif isinstance(entries, dict):
            if "ids" in entries:
                ids_to_check = entries["ids"]
            elif "id" in entries:
                ids_to_check = [entries["id"]]
            else:
                ids_to_check = [v for v in entries.values() if isinstance(v, str)]
        else:
            logger.warning(f"Unexpected registry format for size {size}: {type(entries)}")
            continue

        for dataset_id in ids_to_check:
            if not isinstance(dataset_id, str):
                logger.warning(f"Skipping non‑string ID in size {size}: {dataset_id}")
                continue

            if validate_dataset_id(dataset_id, logger):
                valid_ids.append(dataset_id)
            else:
                invalid_ids.append(dataset_id)

    return {
        "valid_ids": valid_ids,
        "invalid_ids": invalid_ids,
        "all_valid": len(invalid_ids) == 0,
    }

# ----------------------------------------------------------------------
# Output writers
# ----------------------------------------------------------------------
def write_validation_log(log_path: Path, results: Dict[str, Any], registry_path: Path):
    """Write a human‑readable validation log."""
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("Registry Validation Log\n")
        f.write("=======================\n")
        f.write(f"Registry file: {registry_path}\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write(f"Valid IDs ({len(results['valid_ids'])}):\n")
        for vid in results["valid_ids"]:
            f.write(f"  - {vid}\n")

        f.write(f"\nInvalid IDs ({len(results['invalid_ids'])}):\n")
        for iid in results["invalid_ids"]:
            f.write(f"  - {iid}\n")

        overall = "PASS" if results["all_valid"] else "FAIL"
        f.write(f"\nOverall Status: {overall}\n")

        # Explicit line required by the verification step
        if results["all_valid"]:
            f.write("\nVALIDATION SUCCESS\n")
        else:
            f.write("\nVALIDATION FAILED\n")

def write_valid_sources(valid_ids: List[str], output_path: Path):
    """Write the list of validated source IDs to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(valid_ids, f, indent=2)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Execute the registry validation workflow."""
    project_root = get_project_root()
    registry_path = project_root / "data" / "metadata" / "dataset_registry.json"
    log_path = project_root / "data" / "metadata" / "registry_validation.log"
    valid_sources_path = project_root / "data" / "metadata" / "valid_sources.json"

    logger = setup_logger("RegistryValidator", str(log_path))

    logger.info("Starting registry validation...")

    try:
        # Load the registry JSON
        logger.info(f"Loading registry from {registry_path}")
        registry = load_registry(registry_path)

        # Perform validation
        logger.info("Validating dataset IDs...")
        results = validate_registry(registry, logger)

        # Persist outputs
        write_validation_log(log_path, results, registry_path)
        write_valid_sources(results["valid_ids"], valid_sources_path)

        if results["all_valid"]:
            logger.info("All dataset IDs are valid.")
            logger.info("VALIDATION SUCCESS")
            return 0
        else:
            logger.error(
                f"Validation failed. {len(results['invalid_ids'])} invalid IDs found."
            )
            logger.error(
                "HALTING: Please fix the registry or update VERIFIED_DATASET_IDS in config."
            )
            logger.error("VALIDATION FAILED")
            return 1

    except FileNotFoundError as e:
        logger.error(f"FATAL: {e}")
        return 1
    except Exception as e:
        logger.error(f"FATAL: Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
