import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def ensure_directories():
    """Ensure required directories exist."""
    dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "interim",
        DATA_PROCESSED_DIR,
        PROJECT_ROOT / "tests" / "unit",
        PROJECT_ROOT / "tests" / "integration",
        PROJECT_ROOT / "reports"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Directories ensured under {PROJECT_ROOT}")

def get_subject_list(download_log_path: Optional[Path] = None) -> List[str]:
    """
    Extract subject IDs from the download log or a provided list.
    For this implementation, we assume the download process creates a log.
    """
    if download_log_path is None:
        download_log_path = DATA_PROCESSED_DIR / "download_log.json"
    
    if not download_log_path.exists():
        logger.warning(f"Download log not found at {download_log_path}. Returning empty list.")
        return []

    with open(download_log_path, 'r') as f:
        data = json.load(f)
    
    # Assuming the log structure contains a 'subjects' key
    subjects = data.get('subjects', [])
    return [s.get('id') for s in subjects if s.get('id')]

def download_dataset(dataset_id: str, output_dir: Path):
    """
    Placeholder for actual OpenNeuro download logic.
    In a real implementation, this would use openneuro-py or direct API calls.
    """
    logger.info(f"Attempting to download dataset {dataset_id} to {output_dir}")
    # Simulation of download success for the sake of the pipeline flow
    # In reality, this would fetch data
    (output_dir / "downloaded").mkdir(parents=True, exist_ok=True)
    return True

def fetch_fallback_dataset(output_dir: Path):
    """
    Fetch fallback dataset if primary fails.
    """
    logger.warning("Primary dataset unavailable. Fetching fallback.")
    return download_dataset("ds000230", output_dir)

def enforce_sample_limit(subjects: List[str], limit: int = 10) -> List[str]:
    """Enforce the N=10 sample limit."""
    if len(subjects) > limit:
        logger.info(f"Limiting subjects from {len(subjects)} to {limit}")
        return subjects[:limit]
    return subjects

def load_behavioral_scores(subject_dir: Path) -> Optional[float]:
    """
    Load Fluid Intelligence score from a subject's behavioral data.
    Returns None if not found or invalid.
    """
    # Look for common behavioral JSON files
    possible_files = [
        subject_dir / "participants.tsv",
        subject_dir / "sub-01_behavioral.json",
        subject_dir / "behaviors.json"
    ]
    
    for f_path in possible_files:
        if f_path.exists():
            try:
                with open(f_path, 'r') as f:
                    data = json.load(f)
                    # Check for Fluid Intelligence key
                    if 'FluidIntelligence' in data:
                        score = float(data['FluidIntelligence'])
                        if not (0 <= score <= 100): # Basic validation
                            logger.warning(f"Invalid Fluid Intelligence score for {subject_dir.name}")
                            return None
                        return score
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Error parsing behavioral data for {subject_dir.name}: {e}")
    
    return None

def validate_and_aggregate(subjects: List[str], data_dir: Path) -> Dict[str, Any]:
    """
    Validate subjects for Fluid Intelligence scores and aggregate results.
    Writes valid_subjects.json to data/processed.
    """
    valid_subjects = []
    
    for sub_id in subjects:
        sub_dir = data_dir / sub_id
        if sub_dir.exists():
            score = load_behavioral_scores(sub_dir)
            if score is not None:
                valid_subjects.append({"id": sub_id, "score": score})
            else:
                logger.info(f"Subject {sub_id} has no valid Fluid Intelligence score.")
        else:
            logger.warning(f"Subject directory {sub_dir} not found.")
    
    result = {
        "subjects": valid_subjects,
        "count": len(valid_subjects)
    }
    
    output_path = DATA_PROCESSED_DIR / "valid_subjects.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Validation complete. {len(valid_subjects)} valid subjects found.")
    return result

def check_validation_and_halt(valid_subjects_result: Dict[str, Any]) -> None:
    """
    Check if valid subjects count is 0. If so, log error and halt.
    Writes to data/processed/validation_errors.log with prefix [VALIDATION_ERROR].
    """
    count = valid_subjects_result.get("count", 0)
    
    if count == 0:
        error_msg = "No valid Fluid Intelligence data found in specified datasets"
        logger.critical(error_msg)
        
        # Write to validation_errors.log
        log_path = DATA_PROCESSED_DIR / "validation_errors.log"
        with open(log_path, 'a') as f:
            f.write(f"[VALIDATION_ERROR] {error_msg}\n")
        
        raise ValueError(error_msg)
    
    logger.info(f"Validation passed. {count} valid subjects available.")

def fetch_openneuro_data(primary_id: str = "ds000224", fallback_id: str = "ds000230", limit: int = 10):
    """
    Main entry point to fetch, validate, and prepare data.
    """
    ensure_directories()
    
    raw_dir = PROJECT_ROOT / "data" / "raw"
    
    # Try primary
    logger.info(f"Fetching primary dataset: {primary_id}")
    if not download_dataset(primary_id, raw_dir):
        logger.warning("Primary download failed. Trying fallback.")
        if not fetch_fallback_dataset(raw_dir):
            logger.critical("Both primary and fallback datasets failed to download.")
            # Halt logic for download failure could go here if required
            return None
    
    # Get subjects
    subjects = get_subject_list()
    if not subjects:
        # If no subjects found in log, we might need to scan directory
        # For this task, we rely on the log or assume subjects are known
        subjects = [d.name for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    
    # Enforce limit
    subjects = enforce_sample_limit(subjects, limit)
    
    # Validate
    result = validate_and_aggregate(subjects, raw_dir)
    
    # Critical Halt Check
    check_validation_and_halt(result)
    
    return result

def main():
    """Main execution entry."""
    try:
        fetch_openneuro_data()
        logger.info("Data fetch and validation completed successfully.")
    except ValueError as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
