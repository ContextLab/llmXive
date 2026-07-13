import json
import hashlib
import logging
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config
from utils.validators import validate_dataset_schema, SchemaValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_preprocessed_issues(input_path: Path) -> List[Dict[str, Any]]:
    """Load the preprocessed issues from the JSON file."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('issues', [])

def calculate_checksum(data: List[Dict[str, Any]], algorithm: str = 'sha256') -> str:
    """Calculate a deterministic checksum of the dataset."""
    # Serialize data to a canonical JSON string to ensure determinism
    # Sort keys and ensure consistent formatting
    canonical_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    hasher = hashlib.new(algorithm)
    hasher.update(canonical_str.encode('utf-8'))
    return hasher.hexdigest()

def validate_completeness(
    data: List[Dict[str, Any]], 
    required_columns: List[str],
    threshold: float = 0.95
) -> Tuple[bool, float, Dict[str, float]]:
    """
    Validate that the dataset meets the completeness threshold.
    
    Returns:
        Tuple of (is_valid, overall_completeness, column_completeness_map)
    """
    if not data:
        logger.error("Dataset is empty.")
        return False, 0.0, {}

    total_rows = len(data)
    column_completeness = {}
    total_missing = 0
    total_cells = total_rows * len(required_columns)

    for col in required_columns:
        missing_count = sum(1 for row in data if row.get(col) is None or row.get(col) == "")
        column_completeness[col] = 1.0 - (missing_count / total_rows)
        total_missing += missing_count

    overall_completeness = 1.0 - (total_missing / total_cells)
    is_valid = overall_completeness >= threshold

    logger.info(f"Completeness check: {overall_completeness:.2%} (Threshold: {threshold:.2%})")
    for col, comp in column_completeness.items():
        logger.info(f"  {col}: {comp:.2%}")

    return is_valid, overall_completeness, column_completeness

def save_metadata(
    output_path: Path,
    checksum: str,
    completeness: float,
    column_completeness: Dict[str, float],
    row_count: int,
    config: Dict[str, Any]
) -> Path:
    """Save metadata about the cleaned dataset."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "checksum_sha256": checksum,
        "row_count": row_count,
        "completeness": {
            "overall": completeness,
            "threshold": config.get('completeness_threshold', 0.95),
            "passed": completeness >= config.get('completeness_threshold', 0.95),
            "per_column": column_completeness
        },
        "schema_version": "1.0",
        "source_file": config.get('source_file', 'preprocessed_issues.json')
    }

    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata saved to {metadata_path}")
    return metadata_path

def main():
    """Main entry point for saving cleaned data."""
    config = get_config()
    
    # Define paths
    input_file = Path(config.get('paths', {}).get('preprocessed_issues', 
                       PROJECT_ROOT / "data" / "processed" / "preprocessed_issues.json"))
    output_dir = Path(config.get('paths', {}).get('processed_data', 
                       PROJECT_ROOT / "data" / "processed"))
    output_file = output_dir / "cleaned_issues.csv"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading preprocessed issues from {input_file}")
    try:
        issues = load_preprocessed_issues(input_file)
    except FileNotFoundError as e:
        logger.error(f"Failed to load issues: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(issues)} issues")
    
    # Define required columns based on SC-001
    # Assuming the schema defines these required fields
    required_columns = [
        "repository", 
        "issue_number", 
        "created_at", 
        "closed_at", 
        "resolution_time_hours",
        "language",
        "author",
        "title"
    ]
    
    # Validate completeness
    logger.info("Validating dataset completeness...")
    is_valid, completeness, col_completeness = validate_completeness(
        issues, 
        required_columns, 
        threshold=config.get('completeness_threshold', 0.95)
    )
    
    if not is_valid:
        logger.error(f"Dataset completeness {completeness:.2%} is below threshold {config.get('completeness_threshold', 0.95):.2%}. Aborting.")
        # Write a failure state instead of the CSV to prevent downstream errors
        error_state = {
            "status": "failed",
            "reason": "completeness_threshold_not_met",
            "completeness": completeness,
            "threshold": config.get('completeness_threshold', 0.95)
        }
        error_path = output_dir / "cleaning_state_error.json"
        with open(error_path, 'w') as f:
            json.dump(error_state, f, indent=2)
        sys.exit(1)
    
    # Calculate checksum
    logger.info("Calculating dataset checksum...")
    checksum = calculate_checksum(issues)
    logger.info(f"Checksum: {checksum}")
    
    # Write CSV
    logger.info(f"Writing cleaned dataset to {output_file}")
    if issues:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=required_columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(issues)
    
    logger.info(f"Successfully wrote {len(issues)} rows to {output_file}")
    
    # Save metadata
    logger.info("Saving metadata...")
    save_metadata(
        output_file,
        checksum,
        completeness,
        col_completeness,
        len(issues),
        {
            'source_file': str(input_file),
            'completeness_threshold': config.get('completeness_threshold', 0.95)
        }
    )
    
    # Validate against schema if a schema file is defined
    schema_path = Path(config.get('paths', {}).get('schema', 
                       PROJECT_ROOT / "contracts" / "dataset_schema.yaml"))
    if schema_path.exists():
        logger.info(f"Validating against schema {schema_path}")
        try:
            validator = SchemaValidator(schema_path)
            # Convert list of dicts to a simple structure for validation
            # Assuming the validator expects a dict with a list of items
            validation_result = validator.validate({"issues": issues})
            if not validation_result.get('valid', False):
                logger.warning(f"Schema validation warnings: {validation_result.get('errors', [])}")
            else:
                logger.info("Schema validation passed.")
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
    else:
        logger.warning(f"Schema file not found at {schema_path}, skipping schema validation.")
    
    logger.info("Task completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
