import os
import sys
import time
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def ensure_directories() -> None:
    """Create necessary directories for raw, interim, and processed data."""
    dirs = [
        Path("data/raw"),
        Path("data/interim"),
        Path("data/processed"),
        Path("data/external"),
        Path("data/mock")
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def get_subject_list(mock_input: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve the list of subjects.
    
    If --mock-input is provided, load from the specified JSON file.
    Otherwise, attempt to load from the real download log or raise an error.
    
    Args:
        mock_input: Path to the mock subjects JSON file (e.g., data/mock/subjects.json).
                    
    Returns:
        List of subject dictionaries.
        
    Raises:
        FileNotFoundError: If no valid subject source is found.
        RuntimeError: If mock input is requested but file is missing.
    """
    if mock_input:
        logger.warning("⚠️ MOCK INPUT MODE ACTIVE: --mock-input flag invoked. This should NOT be used in production.")
        mock_path = Path(mock_input)
        if not mock_path.exists():
            raise FileNotFoundError(f"Mock input file not found: {mock_path}")
        
        logger.info(f"Loading subject list from mock input: {mock_path}")
        try:
            with open(mock_path, 'r') as f:
                subjects = json.load(f)
            
            # Validate minimal schema
            for sub in subjects:
                if 'id' not in sub:
                    raise ValueError(f"Subject missing 'id' field: {sub}")
                if 'fluid_intelligence_score' not in sub:
                    raise ValueError(f"Subject missing 'fluid_intelligence_score' field: {sub}")
            
            logger.info(f"Loaded {len(subjects)} subjects from mock input.")
            return subjects
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse mock input JSON: {e}")
    
    # Real data path: check if download log exists
    download_log = Path("data/raw/download_log.json")
    if download_log.exists():
        try:
            with open(download_log, 'r') as f:
                data = json.load(f)
            subjects = data.get('subjects', [])
            if subjects:
                logger.info(f"Loaded {len(subjects)} subjects from real download log.")
                return subjects
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse download log: {e}. Falling through to error.")
    
    # If we reach here, no valid source was found
    raise FileNotFoundError(
        "Valid subjects file not found. Run the real download task (T015b) or "
        "provide a mock input file via --mock-input for testing."
    )

def download_dataset(dataset_id: str, output_dir: Path) -> bool:
    """
    Attempt to download a dataset from OpenNeuro.
    
    Args:
        dataset_id: The OpenNeuro dataset ID (e.g., 'ds000224').
        output_dir: Directory to save the data.
                    
    Returns:
        True if download succeeds, False otherwise.
    """
    logger.info(f"Attempting to download dataset: {dataset_id}")
    # Placeholder for real download logic using openneuro-py or similar
    # In a real implementation, this would call the OpenNeuro API
    # For now, we raise an error if not using mock input to enforce real data constraint
    raise NotImplementedError("Real download logic requires 'openneuro-py' or 'bids-validator' integration.")

def fetch_fallback_dataset(output_dir: Path) -> bool:
    """
    Fetch fallback dataset if primary fails.
    
    Args:
        output_dir: Directory to save the data.
                    
    Returns:
        True if fallback succeeds, False otherwise.
    """
    logger.warning("Primary dataset fetch failed. Attempting fallback...")
    return download_dataset("ds000230", output_dir)

def enforce_sample_limit(subjects: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """
    Limit the number of subjects to the specified sample size.
    
    Args:
        subjects: List of subject dictionaries.
        limit: Maximum number of subjects to return.
                    
    Returns:
        Subset of subjects.
    """
    if len(subjects) > limit:
        logger.info(f"Sample size limit ({limit}) applied. Truncating from {len(subjects)} to {limit}.")
        return subjects[:limit]
    return subjects

def load_behavioral_scores(subjects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract and validate behavioral scores from subject list.
    
    Args:
        subjects: List of subject dictionaries.
                    
    Returns:
        List of subjects with validated behavioral scores.
    """
    valid_subjects = []
    for sub in subjects:
        if 'fluid_intelligence_score' in sub and sub['fluid_intelligence_score'] is not None:
            valid_subjects.append(sub)
        else:
            logger.warning(f"Skipping subject {sub.get('id', 'unknown')}: missing fluid_intelligence_score")
    
    logger.info(f"Validated {len(valid_subjects)} subjects with behavioral scores.")
    return valid_subjects

def validate_and_aggregate(subjects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate the subject list and aggregate summary statistics.
    
    Args:
        subjects: List of subject dictionaries.
                    
    Returns:
        Summary dictionary.
    """
    if not subjects:
        raise ValueError("No valid subjects found for analysis.")
    
    scores = [s['fluid_intelligence_score'] for s in subjects]
    return {
        "total_subjects": len(subjects),
        "min_score": min(scores),
        "max_score": max(scores),
        "mean_score": sum(scores) / len(scores),
        "subjects": subjects
    }

def check_validation_and_halt(agg_data: Dict[str, Any]) -> None:
    """
    Check if the aggregated data meets minimum requirements.
    Halts execution if no valid subjects are found.
    
    Args:
        agg_data: Aggregated summary data.
    """
    if agg_data['total_subjects'] == 0:
        logger.critical("HALT: No valid subjects with Fluid Intelligence scores found.")
        sys.exit(1)
    logger.info(f"Validation passed. {agg_data['total_subjects']} subjects ready for processing.")

def fetch_openneuro_data(primary_id: str, fallback_id: str, output_dir: Path) -> Tuple[bool, str]:
    """
    Main entry point for fetching real OpenNeuro data.
    
    Args:
        primary_id: Primary dataset ID.
        fallback_id: Fallback dataset ID.
        output_dir: Output directory for data.
                    
    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        if download_dataset(primary_id, output_dir):
            return True, f"Successfully downloaded {primary_id}"
    except Exception as e:
        logger.warning(f"Primary dataset {primary_id} failed: {e}")
        try:
            if fetch_fallback_dataset(output_dir):
                return True, f"Successfully downloaded fallback {fallback_id}"
        except Exception as e2:
            logger.error(f"Fallback dataset {fallback_id} also failed: {e2}")
    
    return False, "Failed to download any dataset"

def main():
    parser = argparse.ArgumentParser(description="Download and validate OpenNeuro datasets.")
    parser.add_argument(
        "--mock-input",
        type=str,
        default=None,
        help="Path to mock subjects JSON file for testing (e.g., data/mock/subjects.json). "
             "WARNING: Do not use in production."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to save downloaded data (default: data/raw)."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10,
        help="Maximum number of subjects to process (default: 10)."
    )
    
    args = parser.parse_args()
    
    ensure_directories()
    output_dir = Path(args.output_dir)
    
    # 1. Get subject list (Mock or Real)
    try:
        subjects = get_subject_list(mock_input=args.mock_input)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Enforce sample limit
    subjects = enforce_sample_limit(subjects, args.sample_size)
    
    # 3. Load and validate behavioral scores
    valid_subjects = load_behavioral_scores(subjects)
    
    # 4. Aggregate and check
    agg_data = validate_and_aggregate(valid_subjects)
    check_validation_and_halt(agg_data)
    
    # 5. Write aggregated data to processed log
    log_path = output_dir / "aggregated_subjects.json"
    with open(log_path, 'w') as f:
        json.dump(agg_data, f, indent=2)
    
    logger.info(f"Aggregated subject data written to {log_path}")
    logger.info("Download and validation complete.")

if __name__ == "__main__":
    main()
