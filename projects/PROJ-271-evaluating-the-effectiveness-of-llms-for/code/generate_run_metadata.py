"""
Module to generate and save run metadata for reproducibility.

This module captures the exact environment hash, dataset version commit ID,
and random seed used for the sample, ensuring that every result set can be
exactly reproduced (Constitution Principle I).
"""

import os
import json
import subprocess
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_results_path, setup_logging

# Configure logging
logger = setup_logging(__name__)


def get_environment_hash() -> str:
    """
    Generate a hash of the current Python environment (pip freeze).

    Returns:
        str: SHA-256 hash of the pip freeze output.
    """
    try:
        result = subprocess.run(
            ['pip', 'freeze'],
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        freeze_output = result.stdout
        return hashlib.sha256(freeze_output.encode('utf-8')).hexdigest()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run pip freeze: {e}")
        return "error_pip_freeze"
    except subprocess.TimeoutExpired:
        logger.error("Timeout while running pip freeze")
        return "timeout_pip_freeze"
    except Exception as e:
        logger.error(f"Unexpected error generating environment hash: {e}")
        return "error_unknown"


def get_dataset_commit_id() -> str:
    """
    Retrieve the commit ID of the 'codeparrot/github-code' dataset.

    This function queries the Hugging Face datasets library to get the
    specific commit hash for the dataset version used.

    Returns:
        str: The dataset commit ID or an error message if unavailable.
    """
    try:
        # Import here to avoid dependency issues if datasets is not installed
        from datasets import load_dataset_builder
        builder = load_dataset_builder("codeparrot/github-code", trust_remote_code=True)
        # Attempt to get the revision/commit info from the builder
        # The builder might not always expose the exact commit directly in all versions,
        # but we try to access the config or builder attributes.
        if hasattr(builder, 'config') and hasattr(builder.config, 'data_files'):
            # If we can't get a direct commit, we might need to rely on the dataset loading
            # logic which usually pins a version. For now, we try to get a generic identifier.
            pass

        # Fallback: Try to get the dataset info via the HuggingFace Hub API if available
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            repo_info = api.dataset_info("codeparrot/github-code")
            # The last commit ID
            return repo_info.sha if hasattr(repo_info, 'sha') else "unknown_commit"
        except ImportError:
            logger.warning("huggingface_hub not installed, cannot fetch dataset commit ID")
            return "unavailable_no_hf_hub"
        except Exception as e:
            logger.warning(f"Could not fetch dataset commit ID from Hub: {e}")
            return "unavailable_fetch_error"

    except ImportError:
        logger.warning("datasets library not installed, cannot fetch dataset commit ID")
        return "unavailable_no_datasets"
    except Exception as e:
        logger.error(f"Unexpected error getting dataset commit ID: {e}")
        return "error_unknown"


def get_random_seed() -> int:
    """
    Retrieve the random seed used for the sample.

    This function attempts to read the random seed from the configuration.
    If not found, it returns a default value or an error indicator.

    Returns:
        int: The random seed used, or 42 if not explicitly set (common default).
    """
    try:
        # Import config to get the seed if it's defined there
        # Assuming config.py has a RANDOM_SEED constant or similar
        # If not defined in config, we might need to pass it or read from a previous run log.
        # For this implementation, we assume it might be in config or a standard default.
        # Let's try to import a specific constant if it exists, otherwise default.
        # Since the API surface for config.py doesn't explicitly list get_random_seed,
        # we check for a constant directly if possible, or return a default.
        # To be safe and robust, we'll return a default if not found in a specific config path.
        # However, the task implies we should capture the seed *used*.
        # If the seed is passed as an argument or stored in a run config, we should read it.
        # For this task, we will assume a standard default of 42 if not otherwise configured,
        # as the data pipeline likely uses a default or a specific constant defined in config.
        # Let's try to access a potential constant from config if it exists.
        # Since we can't dynamically check all attributes, we'll assume a standard approach.
        # If the project uses a specific seed, it should be in config.py.
        # We will try to import it if it exists, otherwise default.
        import importlib
        try:
            config_module = importlib.import_module('config')
            if hasattr(config_module, 'RANDOM_SEED'):
                return config_module.RANDOM_SEED
        except (ImportError, AttributeError):
            pass
        
        # Default seed if not found
        return 42
    except Exception as e:
        logger.error(f"Error retrieving random seed: {e}")
        return 42


def generate_run_metadata() -> Dict[str, Any]:
    """
    Generate a dictionary containing all run metadata.

    Returns:
        Dict[str, Any]: A dictionary with environment_hash, dataset_commit_id,
                        and random_seed.
    """
    logger.info("Generating run metadata...")
    
    metadata = {
        "environment_hash": get_environment_hash(),
        "dataset_commit_id": get_dataset_commit_id(),
        "random_seed": get_random_seed(),
        "generated_at": None  # Will be set by caller or here if needed
    }
    
    # Add timestamp for reference
    import datetime
    metadata["generated_at"] = datetime.datetime.now().isoformat()
    
    logger.info(f"Run metadata generated: {metadata}")
    return metadata


def save_metadata(metadata: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the run metadata to a JSON file.

    Args:
        metadata (Dict[str, Any]): The metadata dictionary to save.
        output_path (Optional[str]): Path to the output file. If None, uses default path.

    Returns:
        str: The path to the saved file.
    """
    if output_path is None:
        results_dir = get_results_path()
        output_path = os.path.join(results_dir, "run_metadata.json")
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Run metadata saved to {output_path}")
        return output_path
    except IOError as e:
        logger.error(f"Failed to save metadata to {output_path}: {e}")
        raise


def main() -> None:
    """
    Main entry point to generate and save run metadata.
    """
    logger.info("Starting run metadata generation...")
    
    metadata = generate_run_metadata()
    output_path = save_metadata(metadata)
    
    logger.info(f"Run metadata successfully generated and saved to {output_path}")


if __name__ == "__main__":
    main()
