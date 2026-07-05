import argparse
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Ensure utils is on path for imports if running as script
_utils_path = os.path.join(os.path.dirname(__file__), 'utils')
if _utils_path not in sys.path:
    sys.path.insert(0, _utils_path)

try:
    from datasets import load_dataset
except ImportError:
    logging.critical("The 'datasets' package is required. Install with: pip install datasets")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
DATASET_NAME_PRIMARY = "bigcode/the-stack-dedup"
DATASET_NAME_FALLBACK = "code_search_net"
RECONSTRUCTION_ONLY_MODE = "Reconstruction-Only"
STANDARD_MODE = "Standard"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        return ""
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        return ""

def validate_schema(dataset_schema: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if the dataset schema contains the required fields.
    
    Args:
        dataset_schema: The schema dictionary of the dataset.
        required_fields: List of field names that must be present.
        
    Returns:
        Tuple of (is_valid, missing_fields)
    """
    missing_fields = []
    for field in required_fields:
        # Handle nested fields (e.g., 'task.summarization')
        parts = field.split('.')
        current = dataset_schema
        found = True
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                # Handle list indices if necessary, though rare in schema dicts
                found = False
                break
            else:
                found = False
                break
        
        if not found:
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields

def check_fallback_mode(dataset_config: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if the dataset configuration requires 'Reconstruction-Only' mode.
    
    This function checks for the presence of independent annotations required for
    standard evaluation (e.g., 'summarization' or 'bug detection' ground truths).
    If these are missing, it flags the configuration as 'Reconstruction-Only'.
    
    Args:
        dataset_config: The configuration or schema of the loaded dataset.
        
    Returns:
        Tuple of (is_reconstruction_only, mode_name)
    """
    # Define the fields required for standard evaluation
    # Based on FR-003 and US1 requirements
    standard_annotation_fields = [
        'summarization', 
        'bug_detection', 
        'task', # Check if a 'task' field exists that might contain these
        'summary', 
        'ground_truth'
    ]
    
    # Flatten schema keys for easier checking if it's a dict of features
    schema_keys = []
    if isinstance(dataset_config, dict):
        if 'features' in dataset_config:
            schema_keys = list(dataset_config['features'].keys())
        else:
            schema_keys = list(dataset_config.keys())
    
    logger.info(f"Checking dataset schema keys: {schema_keys}")
    
    has_independent_annotations = False
    for field in standard_annotation_fields:
        if field in schema_keys:
            has_independent_annotations = True
            logger.info(f"Found required annotation field: {field}")
            break
    
    # Also check for nested structures if 'task' is present
    if 'task' in schema_keys:
        # If 'task' is a dictionary, check its keys
        task_field = dataset_config.get('features', {}).get('task', {}) or dataset_config.get('task', {})
        if isinstance(task_field, dict):
            if 'summarization' in task_field or 'bug_detection' in task_field:
                has_independent_annotations = True
                logger.info("Found nested annotation fields within 'task'.")

    if not has_independent_annotations:
        logger.warning(
            f"Independent annotations (summarization/bug_detection) not found in dataset schema. "
            f"Switching to '{RECONSTRUCTION_ONLY_MODE}' mode as per FR-003 fallback logic."
        )
        return True, RECONSTRUCTION_ONLY_MODE
    
    logger.info(f"Dataset has independent annotations. Using '{STANDARD_MODE}' mode.")
    return False, STANDARD_MODE

def load_and_verify_dataset(
    dataset_name: str = DATASET_NAME_PRIMARY,
    subset: str = "python",
    split: str = "train",
    max_samples: Optional[int] = 100
) -> Tuple[Optional[Any], str, Dict[str, Any]]:
    """
    Load a dataset from HuggingFace Hub and verify its integrity.
    
    Args:
        dataset_name: Name of the dataset to load.
        subset: Subset of the dataset (e.g., 'python').
        split: Split to load (e.g., 'train').
        max_samples: Optional limit on the number of samples to load for testing.
        
    Returns:
        Tuple of (dataset_object, mode_name, schema_dict)
    """
    logger.info(f"Attempting to load dataset: {dataset_name}, subset: {subset}, split: {split}")
    
    try:
        # Load the dataset
        # Note: Using trust_remote_code=True if needed, but keeping it minimal for now
        dataset = load_dataset(dataset_name, name=subset, split=split, streaming=False)
        
        if max_samples:
            logger.info(f"Sampling {max_samples} rows from the dataset.")
            dataset = dataset.select(range(min(max_samples, len(dataset))))
        
        # Get schema
        schema = dataset.features
        schema_dict = dict(schema) if hasattr(schema, 'keys') else {}
        
        # Check for fallback mode
        is_recon_only, mode = check_fallback_mode(schema_dict)
        
        return dataset, mode, schema_dict
        
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        return None, "", {}

def main():
    parser = argparse.ArgumentParser(description="Download and verify code datasets for complexity analysis.")
    parser.add_argument(
        "--dataset", 
        type=str, 
        default=DATASET_NAME_PRIMARY,
        help=f"Name of the dataset to load (default: {DATASET_NAME_PRIMARY})"
    )
    parser.add_argument(
        "--subset", 
        type=str, 
        default="python",
        help="Subset of the dataset (e.g., 'python')"
    )
    parser.add_argument(
        "--split", 
        type=str, 
        default="train",
        help="Split to load (default: train)"
    )
    parser.add_argument(
        "--max-samples", 
        type=int, 
        default=100,
        help="Maximum number of samples to load for verification (default: 100)"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="data/raw",
        help="Directory to save processed data (default: data/raw)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting data download process for {args.dataset}...")
    
    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load dataset
    dataset, mode, schema = load_and_verify_dataset(
        dataset_name=args.dataset,
        subset=args.subset,
        split=args.split,
        max_samples=args.max_samples
    )
    
    if dataset is None:
        logger.error("Dataset loading failed. Exiting.")
        sys.exit(1)
    
    logger.info(f"Dataset loaded successfully. Mode: {mode}")
    logger.info(f"Schema keys: {list(schema.keys())}")
    
    # Log specific checks for T011b
    if 'summarization' in schema or 'bug_detection' in schema:
        logger.info("Ground truth annotations for 'summarization' and/or 'bug_detection' found.")
    else:
        logger.info("No direct 'summarization' or 'bug_detection' fields found in top-level schema.")
        
    # T011c Logic: If we are in Reconstruction-Only mode, we log this explicitly
    if mode == RECONSTRUCTION_ONLY_MODE:
        logger.warning(
            f"SCOPE CHANGE DETECTED: Dataset configuration is '{RECONSTRUCTION_ONLY_MODE}'. "
            f"Independent annotations are missing. Downstream tasks (T017) will compare generated code "
            f"against the original source code instead of independent ground truths."
        )
    
    # Save a small sample to verify data integrity
    sample_file = output_path / "dataset_sample.json"
    try:
        # Convert first few rows to list for saving
        data_list = []
        for i, row in enumerate(dataset):
            if i >= 10: break
            data_list.append(row)
        
        import json
        with open(sample_file, 'w') as f:
            json.dump(data_list, f, indent=2, default=str)
        
        logger.info(f"Saved sample data to {sample_file}")
        
        # Calculate checksum
        checksum = calculate_sha256(str(sample_file))
        if checksum:
            logger.info(f"Checksum for sample file: {checksum}")
            
    except Exception as e:
        logger.error(f"Failed to save sample data: {e}")
        
    logger.info("Data download and verification complete.")

if __name__ == "__main__":
    main()