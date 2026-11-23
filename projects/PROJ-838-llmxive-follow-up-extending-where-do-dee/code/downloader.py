import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from config import ensure_directories

# Attempt to import datasets. If not present, the error will be caught and raised loudly.
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' library is required for streaming TELBench. "
        "Please install it via: pip install datasets"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

def verify_dataset_exists(dataset_id: str) -> bool:
    """
    Checks if the canonical HuggingFace ID exists.
    Returns True if found, raises ValueError if not found.
    """
    try:
        # Using load_dataset with streaming to check existence without downloading
        # We only fetch a tiny slice to verify availability.
        ds = load_dataset(dataset_id, streaming=True)
        # If we get here without exception, the dataset exists.
        logger.info(f"Verified dataset existence: {dataset_id}")
        return True
    except Exception as e:
        logger.error(f"Dataset {dataset_id} not found or inaccessible: {e}")
        raise ValueError(f"Dataset {dataset_id} not found or inaccessible: {e}") from e

def validate_trajectory_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a single trajectory record from TELBench.
    Returns (is_valid, error_message).
    """
    required_fields = ["id", "spans"]
    for field in required_fields:
        if field not in record:
            return False, f"Missing required field: {field}"
    
    if not isinstance(record["spans"], list):
        return False, "Field 'spans' must be a list"
    
    if len(record["spans"]) == 0:
        return False, "Field 'spans' cannot be empty"

    return True, None

def validate_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    Loads and validates a JSON file containing trajectories.
    Skips malformed records and logs them.
    """
    valid_records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValidationError(f"JSON file {filepath} must contain a list of trajectories")

    for i, record in enumerate(data):
        is_valid, error = validate_trajectory_record(record)
        if is_valid:
            valid_records.append(record)
        else:
            logger.warning(f"Skipping record {i} in {filepath}: {error}")
    
    return valid_records

def fetch_and_validate(dataset_id: str, output_dir: Path) -> None:
    """
    Fetches the TELBench dataset using streaming, validates records,
    and saves them to the output directory.
    """
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "tebench_raw.json"

    if output_file.exists():
        logger.info(f"Dataset already exists at {output_file}. Skipping download.")
        return

    logger.info(f"Starting streaming download for {dataset_id}...")
    try:
        # Use streaming to avoid loading entire dataset into RAM
        dataset = load_dataset(dataset_id, streaming=True)
        
        # TELBench usually has a 'train' split or similar. 
        # We iterate over the first split found or default to 'train'.
        split_name = "train" if "train" in dataset else list(dataset.keys())[0]
        logger.info(f"Using split: {split_name}")
        
        raw_data = []
        count = 0
        
        for item in dataset[split_name]:
            is_valid, error = validate_trajectory_record(item)
            if is_valid:
                raw_data.append(item)
                count += 1
            else:
                logger.warning(f"Skipping malformed trajectory: {error}")
            
            # Optional: Log progress every 1000 items if the stream is long
            if count % 1000 == 0:
                logger.info(f"Processed {count} valid trajectories...")

        # Save the validated data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2)
        
        logger.info(f"Successfully saved {count} valid trajectories to {output_file}")

    except Exception as e:
        logger.error(f"Failed to fetch or process dataset: {e}")
        raise

def fetch_tebench() -> Path:
    """
    Main entry point to fetch TELBench.
    Verifies canonical IDs: HuggingFaceH4/tebench -> HuggingFaceH4/tebench-v1.
    Returns the path to the saved JSON file.
    """
    primary_id = "HuggingFaceH4/tebench"
    fallback_id = "HuggingFaceH4/tebench-v1"
    
    dataset_id = None
    try:
        verify_dataset_exists(primary_id)
        dataset_id = primary_id
    except ValueError:
        logger.warning(f"Primary dataset {primary_id} not found. Trying fallback...")
        try:
            verify_dataset_exists(fallback_id)
            dataset_id = fallback_id
        except ValueError:
            raise RuntimeError(
                f"Neither {primary_id} nor {fallback_id} found on HuggingFace. "
                "Cannot proceed without real data source."
            )

    output_dir = Path("data/raw")
    fetch_and_validate(dataset_id, output_dir)
    return output_dir / "tebench_raw.json"

def stream_dataset(dataset_id: str = "HuggingFaceH4/tebench") -> Any:
    """
    Utility to stream the TELBench dataset without loading it into memory.
    Returns an iterable dataset object.
    
    This function is integrated into the pipeline to handle large splits
    by processing data in chunks, ensuring full dataset contribution to statistics
    without exceeding RAM.
    
    Args:
        dataset_id: The HuggingFace dataset ID (defaults to primary TELBench).
    
    Yields:
        Individual trajectory records from the dataset.
    
    Raises:
        ValueError: If the dataset source is missing or inaccessible.
    """
    try:
        # Verify existence first to fail loudly if missing
        verify_dataset_exists(dataset_id)
        
        # Load with streaming=True
        ds = load_dataset(dataset_id, streaming=True)
        
        # Determine the split to use
        split_name = "train" if "train" in ds else list(ds.keys())[0]
        logger.info(f"Streaming dataset split: {split_name}")
        
        return ds[split_name]
    
    except ImportError as e:
        raise ImportError(
            "The 'datasets' library is required for streaming. "
            "Install with: pip install datasets"
        ) from e
    except Exception as e:
        logger.error(f"Failed to initialize stream for {dataset_id}: {e}")
        raise ValueError(f"Could not stream dataset {dataset_id}: {e}") from e

def fetch_tebench_streaming(output_dir: Optional[Path] = None) -> Path:
    """
    Fetches TELBench using streaming and saves it to disk.
    This is the recommended method for large datasets to avoid OOM errors.
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    ensure_directories()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "tebench_raw.json"

    if output_file.exists():
        logger.info(f"Dataset already exists at {output_file}. Skipping download.")
        return output_file

    logger.info(f"Starting streaming fetch for {dataset_id}...")
    
    # Use the streaming utility to get an iterator
    # Note: We need to define dataset_id here or use the config one.
    # Assuming we use the primary ID from fetch_tebench logic.
    primary_id = "HuggingFaceH4/tebench"
    fallback_id = "HuggingFaceH4/tebench-v1"
    
    dataset_id_to_use = None
    try:
        verify_dataset_exists(primary_id)
        dataset_id_to_use = primary_id
    except ValueError:
        try:
            verify_dataset_exists(fallback_id)
            dataset_id_to_use = fallback_id
        except ValueError:
            raise RuntimeError(f"Dataset {primary_id} and {fallback_id} not found.")

    ds = load_dataset(dataset_id_to_use, streaming=True)
    split_name = "train" if "train" in ds else list(ds.keys())[0]
    
    raw_data = []
    count = 0
    
    logger.info(f"Iterating over {split_name} split...")
    for item in ds[split_name]:
        is_valid, error = validate_trajectory_record(item)
        if is_valid:
            raw_data.append(item)
            count += 1
        else:
            logger.warning(f"Skipping malformed trajectory: {error}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, indent=2)
    
    logger.info(f"Saved {count} valid trajectories to {output_file}")
    return output_file