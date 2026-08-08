import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import ResourceMonitor from utils as per API surface
from utils import ResourceMonitor
from config import get_sample_limit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/pipeline_errors.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Thresholds from task specification
TRANSLATION_THRESHOLD_MM = 3.0
ROTATION_THRESHOLD_MM = 2.0

def load_motion_metrics(subject_id: str, data_dir: Path) -> Optional[Dict[str, float]]:
    """
    Load motion metrics for a subject from the preprocessing logs.
    Expects a JSON file named {subject_id}_motion_metrics.json in data_dir.
    
    Args:
        subject_id: The subject identifier
        data_dir: Path to the data directory containing motion metrics
        
    Returns:
        Dictionary with 'translation_mm' and 'rotation_mm' keys, or None if not found
    """
    motion_file = data_dir / f"{subject_id}_motion_metrics.json"
    if not motion_file.exists():
        logger.warning(f"Motion metrics file not found for subject {subject_id}")
        return None
    
    try:
        with open(motion_file, 'r') as f:
            data = json.load(f)
        return {
            'translation_mm': float(data.get('translation_mm', 0.0)),
            'rotation_mm': float(data.get('rotation_mm', 0.0))
        }
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Error parsing motion metrics for {subject_id}: {e}")
        return None

def get_valid_subjects(valid_subjects_file: Path) -> List[str]:
    """
    Load the list of valid subjects from the validation output.
    
    Args:
        valid_subjects_file: Path to valid_subjects.json
        
    Returns:
        List of subject IDs
    """
    if not valid_subjects_file.exists():
        raise FileNotFoundError(f"Valid subjects file not found: {valid_subjects_file}")
    
    with open(valid_subjects_file, 'r') as f:
        data = json.load(f)
    
    return [s['id'] for s in data.get('subjects', [])]

def detect_motion_artifacts(
    subjects: List[str],
    data_dir: Path,
    output_file: Path,
    translation_threshold: float = TRANSLATION_THRESHOLD_MM,
    rotation_threshold: float = ROTATION_THRESHOLD_MM
) -> List[Dict[str, Any]]:
    """
    Detect excessive motion artifacts for a list of subjects.
    
    Args:
        subjects: List of subject IDs to process
        data_dir: Directory containing motion metrics
        output_file: Path to write the CSV output
        translation_threshold: Maximum allowed translation in mm
        rotation_threshold: Maximum allowed rotation in mm
        
    Returns:
        List of dictionaries with subject motion data
    """
    results = []
    
    for subject_id in subjects:
        metrics = load_motion_metrics(subject_id, data_dir)
        
        if metrics is None:
            # If no metrics found, we cannot determine exclusion status
            # Mark as excluded to be safe, or log a warning
            logger.warning(f"No motion metrics found for {subject_id}, excluding from analysis")
            results.append({
                'subject_id': subject_id,
                'translation_mm': None,
                'rotation_mm': None,
                'excluded': True
            })
            continue
        
        translation = metrics['translation_mm']
        rotation = metrics['rotation_mm']
        
        # Determine if subject should be excluded based on thresholds
        # Translation > 3mm OR Rotation > 2mm
        excluded = (translation > translation_threshold) or (rotation > rotation_threshold)
        
        results.append({
            'subject_id': subject_id,
            'translation_mm': translation,
            'rotation_mm': rotation,
            'excluded': excluded
        })
        
        if excluded:
            logger.info(f"Subject {subject_id} excluded due to motion: "
                      f"translation={translation:.2f}mm, rotation={rotation:.2f}mm")
        else:
            logger.info(f"Subject {subject_id} passed motion check: "
                      f"translation={translation:.2f}mm, rotation={rotation:.2f}mm")
    
    return results

def write_motion_exclusion_log(results: List[Dict[str, Any]], output_file: Path):
    """
    Write the motion exclusion results to a CSV file.
    
    Args:
        results: List of motion analysis results
        output_file: Path to the output CSV file
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subject_id', 'translation_mm', 'rotation_mm', 'excluded'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Motion exclusion log written to {output_file}")

def main():
    """
    Main entry point for motion artifact detection.
    
    This script:
    1. Loads the list of valid subjects from data/processed/valid_subjects.json
    2. Reads motion metrics for each subject
    3. Applies exclusion thresholds (Translation > 3mm OR Rotation > 2mm)
    4. Writes results to data/processed/motion_exclusion_log.csv
    """
    # Initialize resource monitor
    resource_monitor = ResourceMonitor()
    resource_monitor.start()
    
    # Define paths
    data_dir = Path("data/processed")
    valid_subjects_file = data_dir / "valid_subjects.json"
    output_file = data_dir / "motion_exclusion_log.csv"
    
    try:
        # Load valid subjects
        logger.info(f"Loading valid subjects from {valid_subjects_file}")
        subjects = get_valid_subjects(valid_subjects_file)
        logger.info(f"Found {len(subjects)} valid subjects")
        
        if len(subjects) == 0:
            logger.error("No valid subjects found. Cannot proceed with motion detection.")
            return
        
        # Detect motion artifacts
        logger.info("Starting motion artifact detection...")
        results = detect_motion_artifacts(
            subjects=subjects,
            data_dir=data_dir,
            output_file=output_file
        )
        
        # Write results
        write_motion_exclusion_log(results, output_file)
        
        # Log summary
        excluded_count = sum(1 for r in results if r['excluded'])
        included_count = len(results) - excluded_count
        logger.info(f"Motion detection complete: {included_count} included, {excluded_count} excluded")
        
    except Exception as e:
        logger.error(f"Error during motion artifact detection: {e}", exc_info=True)
        raise
    finally:
        resource_monitor.stop()

if __name__ == "__main__":
    main()
