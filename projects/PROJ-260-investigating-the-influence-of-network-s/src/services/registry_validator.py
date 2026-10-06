import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Set

# Import from local project structure
from src.lib.config import get_project_root, get_config

# Configure logger
def setup_logger(name: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def load_registry(registry_path: Path) -> Dict[str, Any]:
    """Load the dataset registry JSON."""
    if not registry_path.exists():
        raise FileNotFoundError(f"Registry file not found: {registry_path}")
    
    with open(registry_path, 'r') as f:
        return json.load(f)

def validate_dataset_id(dataset_id: str, logger: logging.Logger) -> bool:
    """
    Validate a dataset ID by checking its reachability.
    For Hugging Face datasets, we attempt to access the dataset info.
    For Zenodo, we check the API endpoint.
    
    Returns True if valid, False otherwise.
    """
    # Determine the type of source based on ID format or config
    # Assuming IDs are HuggingFace dataset names or Zenodo IDs
    
    # Simple heuristic: if it looks like a Zenodo ID (numeric), check Zenodo API
    # Otherwise, assume HuggingFace
    
    is_zenodo = dataset_id.isdigit() or 'zenodo' in dataset_id.lower()
    
    if is_zenodo:
        return validate_zenodo_id(dataset_id, logger)
    else:
        return validate_hf_id(dataset_id, logger)

def validate_zenodo_id(dataset_id: str, logger: logging.Logger) -> bool:
    """Validate a Zenodo dataset ID."""
    import requests
    
    url = f"https://zenodo.org/api/records/{dataset_id}"
    try:
        logger.debug(f"Checking Zenodo ID {dataset_id} at {url}")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # Basic validation: check if it has a 'title' or 'metadata'
            if 'metadata' in data:
                logger.info(f"Zenodo ID {dataset_id} is valid.")
                return True
            else:
                logger.warning(f"Zenodo ID {dataset_id} returned 200 but no metadata.")
                return False
        else:
            logger.warning(f"Zenodo ID {dataset_id} returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.error(f"Network error checking Zenodo ID {dataset_id}: {e}")
        return False
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON response for Zenodo ID {dataset_id}")
        return False

def validate_hf_id(dataset_id: str, logger: logging.Logger) -> bool:
    """Validate a HuggingFace dataset ID."""
    try:
        from datasets import get_dataset_config_names
        
        logger.debug(f"Checking HF dataset {dataset_id}")
        # Attempt to get config names to verify existence
        # This is a lightweight check compared to loading the full dataset
        try:
            configs = get_dataset_config_names(dataset_id)
            logger.info(f"HF dataset {dataset_id} is valid. Configs: {configs}")
            return True
        except Exception as e:
            logger.warning(f"HF dataset {dataset_id} check failed: {e}")
            return False
    except ImportError:
        logger.error("The 'datasets' library is required for HF validation but not installed.")
        return False
    except Exception as e:
        logger.error(f"Error validating HF dataset {dataset_id}: {e}")
        return False

def validate_registry(registry: Dict[str, Any], logger: logging.Logger) -> Dict[str, Any]:
    """
    Validate all dataset IDs in the registry.
    Returns a dictionary with validation results.
    """
    valid_ids: List[str] = []
    invalid_ids: List[str] = []
    
    # The registry is expected to be a dict where keys are system sizes
    # and values are lists of dataset IDs or dicts containing IDs
    for size, entries in registry.items():
        logger.info(f"Validating entries for system size {size}")
        
        if isinstance(entries, list):
            # List of IDs
            ids_to_check = entries
        elif isinstance(entries, dict):
            # Dict might contain 'ids' key or be a single entry
            if 'ids' in entries:
                ids_to_check = entries['ids']
            else:
                # Assume the dict itself represents an entry with an 'id' field
                if 'id' in entries:
                    ids_to_check = [entries['id']]
                else:
                    # Fallback: check all values that are strings
                    ids_to_check = [v for v in entries.values() if isinstance(v, str)]
        else:
            logger.warning(f"Unexpected format for system size {size}: {type(entries)}")
            continue
        
        for dataset_id in ids_to_check:
            if not isinstance(dataset_id, str):
                logger.warning(f"Skipping non-string ID in size {size}: {dataset_id}")
                continue
            
            if validate_dataset_id(dataset_id, logger):
                valid_ids.append(dataset_id)
            else:
                invalid_ids.append(dataset_id)
    
    return {
        'valid_ids': valid_ids,
        'invalid_ids': invalid_ids,
        'all_valid': len(invalid_ids) == 0
    }

def write_validation_log(log_path: Path, results: Dict[str, Any], registry_path: Path):
    """Write the validation log."""
    with open(log_path, 'w') as f:
        f.write(f"Registry Validation Log\n")
        f.write(f"=======================\n")
        f.write(f"Registry file: {registry_path}\n")
        f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"Valid IDs ({len(results['valid_ids'])}):\n")
        for vid in results['valid_ids']:
            f.write(f"  - {vid}\n")
        
        f.write(f"\nInvalid IDs ({len(results['invalid_ids'])}):\n")
        for iid in results['invalid_ids']:
            f.write(f"  - {iid}\n")
        
        f.write(f"\nOverall Status: {'PASS' if results['all_valid'] else 'FAIL'}\n")

def write_valid_sources(valid_ids: List[str], output_path: Path):
    """Write the list of valid source IDs to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(valid_ids, f, indent=2)

def main():
    """Main entry point for registry validation."""
    project_root = get_project_root()
    registry_path = project_root / "data" / "metadata" / "dataset_registry.json"
    log_path = project_root / "data" / "metadata" / "registry_validation.log"
    valid_sources_path = project_root / "data" / "metadata" / "valid_sources.json"
    
    logger = setup_logger("RegistryValidator", str(log_path))
    
    logger.info("Starting registry validation...")
    
    try:
        # Load registry
        logger.info(f"Loading registry from {registry_path}")
        registry = load_registry(registry_path)
        
        # Validate
        logger.info("Validating dataset IDs...")
        results = validate_registry(registry, logger)
        
        # Write logs
        write_validation_log(log_path, results, registry_path)
        
        # Write valid sources
        write_valid_sources(results['valid_ids'], valid_sources_path)
        
        if results['all_valid']:
            logger.info("All dataset IDs are valid.")
            return 0
        else:
            logger.error(f"Validation failed. {len(results['invalid_ids'])} invalid IDs found.")
            logger.error("HALTING: Please fix the registry or update VERIFIED_DATASET_IDS in config.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"FATAL: {e}")
        return 1
    except Exception as e:
        logger.error(f"FATAL: Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
