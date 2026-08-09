import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Thresholds defined in task T018a
TRANSLATION_THRESHOLD_MM = 3.0
ROTATION_THRESHOLD_MM = 2.0

def load_motion_metrics(subject_logs_dir: Path) -> List[Dict[str, Any]]:
    """
    Load motion metrics from preprocessing logs or JSON files.
    Expected format in logs: 'Motion Translation: X mm', 'Motion Rotation: Y mm'
    or a JSON file per subject with keys 'translation_mm', 'rotation_mm'.
    """
    metrics = []
    if not subject_logs_dir.exists():
        logger.warning(f"Subject logs directory not found: {subject_logs_dir}")
        return metrics

    # Try to find JSON logs first (preferred structured format)
    json_files = list(subject_logs_dir.glob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                subject_id = data.get('subject_id', json_file.stem)
                translation = data.get('translation_mm')
                rotation = data.get('rotation_mm')
                
                if translation is not None and rotation is not None:
                    metrics.append({
                        'subject_id': subject_id,
                        'translation_mm': float(translation),
                        'rotation_mm': float(rotation),
                        'source_file': str(json_file)
                    })
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Could not parse motion metrics from {json_file}: {e}")

    # Fallback: Parse text logs if no JSON found
    log_files = list(subject_logs_dir.glob("*.log"))
    if not metrics and log_files:
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    # Simple regex-like parsing for expected log format
                    import re
                    trans_match = re.search(r'Motion Translation:\s*([\d.]+)\s*mm', content)
                    rot_match = re.search(r'Motion Rotation:\s*([\d.]+)\s*mm', content)
                    
                    if trans_match and rot_match:
                        subject_id = log_file.stem
                        metrics.append({
                            'subject_id': subject_id,
                            'translation_mm': float(trans_match.group(1)),
                            'rotation_mm': float(rot_match.group(1)),
                            'source_file': str(log_file)
                        })
            except Exception as e:
                logger.warning(f"Could not parse motion metrics from {log_file}: {e}")

    return metrics

def get_valid_subjects(motion_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter subjects that have valid motion metrics (non-null values).
    """
    return [
        m for m in motion_metrics 
        if m.get('translation_mm') is not None and m.get('rotation_mm') is not None
    ]

def detect_motion_artifacts(motion_metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect subjects with excessive motion based on thresholds.
    Returns list of subjects with exclusion flag.
    """
    results = []
    for metric in motion_metrics:
        translation = metric['translation_mm']
        rotation = metric['rotation_mm']
        
        # Exclude if Translation > 3mm OR Rotation > 2mm
        excluded = (translation > TRANSLATION_THRESHOLD_MM) or (rotation > ROTATION_THRESHOLD_MM)
        
        results.append({
            'subject_id': metric['subject_id'],
            'translation_mm': translation,
            'rotation_mm': rotation,
            'excluded': excluded
        })
        
        if excluded:
            logger.warning(
                f"Subject {metric['subject_id']} excluded due to excessive motion: "
                f"Translation={translation}mm (>{TRANSLATION_THRESHOLD_MM}mm) or "
                f"Rotation={rotation}mm (>{ROTATION_THRESHOLD_MM}mm)"
            )
        else:
            logger.info(
                f"Subject {metric['subject_id']} passed motion check: "
                f"Translation={translation}mm, Rotation={rotation}mm"
            )
    
    return results

def write_motion_exclusion_log(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write motion exclusion results to CSV file.
    Columns: subject_id, translation_mm, rotation_mm, excluded (bool)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['subject_id', 'translation_mm', 'rotation_mm', 'excluded']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow({
                'subject_id': result['subject_id'],
                'translation_mm': f"{result['translation_mm']:.4f}",
                'rotation_mm': f"{result['rotation_mm']:.4f}",
                'excluded': result['excluded']
            })
    
    logger.info(f"Motion exclusion log written to {output_path}")
    logger.info(f"Total subjects processed: {len(results)}")
    logger.info(f"Subjects excluded: {sum(1 for r in results if r['excluded'])}")
    logger.info(f"Subjects retained: {sum(1 for r in results if not r['excluded'])}")

def main():
    """
    Main entry point for motion artifact detection.
    Reads preprocessing logs, detects motion artifacts, and writes exclusion log.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    subject_logs_dir = project_root / "data" / "processed"
    output_csv = project_root / "data" / "processed" / "motion_exclusion_log.csv"
    
    logger.info("Starting motion artifact detection...")
    
    # Load motion metrics from preprocessing outputs
    motion_metrics = load_motion_metrics(subject_logs_dir)
    
    if not motion_metrics:
        logger.warning("No motion metrics found. Creating empty exclusion log.")
        # Create empty CSV with headers
        write_motion_exclusion_log([], output_csv)
        return
    
    # Filter to valid subjects
    valid_subjects = get_valid_subjects(motion_metrics)
    
    if not valid_subjects:
        logger.warning("No valid subjects with motion metrics found.")
        write_motion_exclusion_log([], output_csv)
        return
    
    logger.info(f"Found {len(valid_subjects)} subjects with motion metrics")
    
    # Detect motion artifacts
    exclusion_results = detect_motion_artifacts(valid_subjects)
    
    # Write results to CSV
    write_motion_exclusion_log(exclusion_results, output_csv)
    
    logger.info("Motion artifact detection completed successfully.")

if __name__ == "__main__":
    main()
