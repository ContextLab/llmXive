import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler('data/processed/motion_exclusion.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Thresholds defined in task T018a
TRANSLATION_THRESHOLD_MM = 3.0
ROTATION_THRESHOLD_MM = 2.0

def load_motion_metrics(preprocessed_dir: Path) -> List[Dict[str, Any]]:
    """
    Load motion metrics from preprocessed subject logs.
    Expects logs in data/processed/ containing JSON files with motion data,
    or a consolidated log from preprocessing.
    
    For this implementation, we assume preprocessing (T017) generates
    a motion_metrics.json or individual subject logs with motion data.
    We will look for a file named 'motion_metrics.json' in the processed dir,
    or scan for subject-specific logs if that doesn't exist.
    """
    motion_data = []
    motion_json_path = preprocessed_dir / "motion_metrics.json"
    
    if motion_json_path.exists():
        logger.info(f"Loading motion metrics from {motion_json_path}")
        with open(motion_json_path, 'r') as f:
            data = json.load(f)
            # Normalize to list of dicts
            if isinstance(data, list):
                motion_data = data
            elif isinstance(data, dict) and 'subjects' in data:
                motion_data = data['subjects']
            else:
                # Assume single subject or raw dict
                motion_data = [data] if isinstance(data, dict) else []
    else:
        # Fallback: scan for individual subject motion logs
        logger.warning(f"No central motion_metrics.json found. Scanning {preprocessed_dir} for subject logs.")
        subject_files = list(preprocessed_dir.glob("subject_*_motion.json"))
        for sf in sorted(subject_files):
            try:
                with open(sf, 'r') as f:
                    motion_data.append(json.load(f))
            except Exception as e:
                logger.error(f"Failed to read {sf}: {e}")
    
    if not motion_data:
        logger.warning("No motion metrics found. Returning empty list.")
    
    return motion_data

def get_valid_subjects(motion_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter subjects based on motion thresholds.
    Returns subjects where translation <= 3mm AND rotation <= 2mm.
    """
    valid = []
    for subject in motion_data:
        sub_id = subject.get('subject_id', 'unknown')
        trans = subject.get('translation_mm', 0.0)
        rot = subject.get('rotation_mm', 0.0)
        
        # Check thresholds
        is_excluded = (trans > TRANSLATION_THRESHOLD_MM) or (rot > ROTATION_THRESHOLD_MM)
        
        subject['excluded'] = is_excluded
        valid.append(subject)
        
        if is_excluded:
            logger.info(f"Subject {sub_id} EXCLUDED: trans={trans:.2f}mm, rot={rot:.2f}mm")
        else:
            logger.info(f"Subject {sub_id} INCLUDED: trans={trans:.2f}mm, rot={rot:.2f}mm")
    
    return valid

def detect_motion_artifacts(motion_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect motion artifacts and flag subjects for exclusion.
    This is an alias for get_valid_subjects but kept for API clarity.
    """
    return get_valid_subjects(motion_data)

def write_motion_exclusion_log(processed_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the motion exclusion log to CSV.
    Columns: subject_id, translation_mm, rotation_mm, excluded (bool)
    """
    if not processed_data:
        logger.warning("No data to write to motion exclusion log.")
        # Create empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id', 'translation_mm', 'rotation_mm', 'excluded'])
        return

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['subject_id', 'translation_mm', 'rotation_mm', 'excluded'])
        
        for row in processed_data:
            sub_id = row.get('subject_id', 'unknown')
            trans = row.get('translation_mm', 0.0)
            rot = row.get('rotation_mm', 0.0)
            excluded = row.get('excluded', False)
            
            writer.writerow([sub_id, f"{trans:.4f}", f"{rot:.4f}", excluded])
    
    logger.info(f"Motion exclusion log written to {output_path}")

def main():
    """
    Main entry point for T018a: Motion Artifact Detection.
    1. Load motion metrics from preprocessed data.
    2. Detect artifacts (exclusion logic).
    3. Write CSV output.
    """
    base_dir = Path("data")
    processed_dir = base_dir / "processed"
    output_file = processed_dir / "motion_exclusion_log.csv"
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Motion Artifact Detection (T018a)...")
    
    # Load data
    motion_data = load_motion_metrics(processed_dir)
    
    if not motion_data:
        logger.error("No motion data found. Cannot proceed with exclusion.")
        # Write empty log with headers
        write_motion_exclusion_log([], output_file)
        return
    
    # Detect artifacts / filter
    processed_data = detect_motion_artifacts(motion_data)
    
    # Write output
    write_motion_exclusion_log(processed_data, output_file)
    
    # Summary
    total = len(processed_data)
    excluded_count = sum(1 for d in processed_data if d.get('excluded', False))
    included_count = total - excluded_count
    
    logger.info(f"Motion Detection Complete. Total: {total}, Included: {included_count}, Excluded: {excluded_count}")
    logger.info(f"Output saved to: {output_file}")

if __name__ == "__main__":
    main()
