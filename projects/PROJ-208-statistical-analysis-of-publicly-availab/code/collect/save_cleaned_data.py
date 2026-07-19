import json
import hashlib
import logging
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import from existing API surface
from utils.config import get_config, get_path
from utils.validators import validate_dataset_schema, ensure_contracts_dir

def load_preprocessed_issues(input_path: Path) -> List[Dict[str, Any]]:
    """Load the preprocessed issues from a JSON file."""
    if not input_path.exists():
        raise FileNotFoundError(f"Preprocessed issues file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'issues' in data:
        return data['issues']
    else:
        raise ValueError(f"Unexpected data format in {input_path}")

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_completeness(issues: List[Dict[str, Any]], threshold: float = 0.95) -> Tuple[bool, float, Dict[str, int]]:
    """
    Validate that the dataset meets the completeness threshold.
    
    Args:
        issues: List of issue dictionaries
        threshold: Minimum required completeness ratio (default 0.95)
        
    Returns:
        Tuple of (passed, actual_completeness, missing_counts)
    """
    required_fields = ['issue_id', 'repository', 'resolution_time_hours', 'created_at', 'closed_at']
    
    if not issues:
        raise ValueError("Cannot validate completeness on empty dataset")
    
    total_issues = len(issues)
    missing_counts = {field: 0 for field in required_fields}
    
    for issue in issues:
        for field in required_fields:
            if field not in issue or issue[field] is None:
                missing_counts[field] += 1
    
    # Calculate completeness: 1 - (average missing rate across fields)
    total_missing = sum(missing_counts.values())
    max_possible_missing = total_issues * len(required_fields)
    
    if max_possible_missing == 0:
        completeness = 1.0
    else:
        completeness = 1.0 - (total_missing / max_possible_missing)
    
    passed = completeness >= threshold
    
    logging.info(f"Completeness validation: {completeness:.2%} (threshold: {threshold:.2%})")
    logging.info(f"Missing counts: {missing_counts}")
    
    return passed, completeness, missing_counts

def save_metadata(output_path: Path, checksum: str, completeness: float, 
                 missing_counts: Dict[str, int], total_issues: int):
    """Save metadata about the cleaned dataset."""
    metadata = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'checksum': checksum,
        'completeness': completeness,
        'threshold_met': completeness >= 0.95,
        'total_issues': total_issues,
        'missing_counts': missing_counts,
        'schema_version': '1.0.0'
    }
    
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logging.info(f"Metadata saved to {metadata_path}")

def main():
    """Main entry point for saving cleaned data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/preprocessing.log')
        ]
    )
    
    config = get_config()
    input_path = get_path('preprocessed_issues')
    output_path = get_path('cleaned_issues')
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Loading preprocessed issues from {input_path}")
    issues = load_preprocessed_issues(input_path)
    logging.info(f"Loaded {len(issues)} issues")
    
    # Validate completeness
    logging.info("Validating completeness...")
    passed, completeness, missing_counts = validate_completeness(issues)
    
    if not passed:
        error_msg = f"Completeness {completeness:.2%} is below threshold 95%."
        logging.error(error_msg)
        raise ValueError(error_msg)
    
    # Save to CSV
    logging.info(f"Saving cleaned dataset to {output_path}")
    
    if issues:
        fieldnames = list(issues[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(issues)
    
    # Calculate checksum
    checksum = calculate_checksum(output_path)
    logging.info(f"Checksum: {checksum}")
    
    # Save metadata
    save_metadata(output_path, checksum, completeness, missing_counts, len(issues))
    
    # Save checksum file
    checksum_path = output_path.with_suffix('.sha256')
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    logging.info(f"Checksum saved to {checksum_path}")
    
    logging.info(f"Successfully saved {len(issues)} issues to {output_path}")
    logging.info(f"Completeness: {completeness:.2%} (threshold: 95%)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
