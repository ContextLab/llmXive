import os
import sys
import json
import csv
import logging
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for schema
LABELS_COLUMNS = ['clip_id', 'label', 'reason', 'confidence_score', 'perturbation_type']
EXCLUDED_COLUMNS = ['clip_id', 'reason', 'confidence_score']
CONFIDENCE_THRESHOLD = 0.9

def load_json_file(filepath: str) -> dict:
    """Load a JSON file and return its contents."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_temp_labels(filepath: str) -> list:
    """
    Load temporary labels from a CSV (labels_raw.csv).
    Expected columns: clip_id, label, reason, confidence_score, perturbation_type
    Returns a list of dictionaries.
    """
    path = Path(filepath)
    if not path.exists():
        # If raw labels don't exist, return empty list (will result in empty outputs)
        logger.warning(f"Temporary labels file not found: {filepath}. Proceeding with empty list.")
        return []
    
    rows = []
    with open(path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure types are correct
            if 'confidence_score' in row:
                try:
                    row['confidence_score'] = float(row['confidence_score'])
                except (ValueError, TypeError):
                    row['confidence_score'] = 0.0
            if 'perturbation_type' in row:
                try:
                    row['perturbation_type'] = int(row['perturbation_type'])
                except (ValueError, TypeError):
                    row['perturbation_type'] = 0
            rows.append(row)
    return rows

def process_labels_and_exclusions(temp_labels: list, threshold: float = CONFIDENCE_THRESHOLD) -> tuple:
    """
    Process temporary labels to:
    1. Identify samples with confidence < threshold or label indicating failure (e.g., 'null' already, or specific error reasons).
    2. Assign 'null' label to these samples if not already null.
    3. Separate excluded samples for the log.
    
    Returns:
        tuple: (processed_labels_list, excluded_samples_list)
    """
    processed = []
    excluded = []
    
    for row in temp_labels:
        clip_id = row.get('clip_id', 'unknown')
        confidence = row.get('confidence_score', 0.0)
        current_label = row.get('label', '')
        current_reason = row.get('reason', '')
        perturbation_type = row.get('perturbation_type', 0)
        
        # Determine if this sample should be excluded/flagged as null
        # Criteria: confidence < threshold OR simulation failure indicated in reason/label
        is_low_confidence = confidence < threshold
        is_simulation_failure = 'simulation_failed' in current_reason.lower() or 'failed' in current_reason.lower()
        is_already_null = current_label == 'null'
        
        needs_null_assignment = (is_low_confidence or is_simulation_failure) and not is_already_null
        
        if needs_null_assignment:
            # Update the label to 'null'
            new_label = 'null'
            new_reason = current_reason if current_reason else 'Low confidence or simulation failure'
            new_confidence = confidence
            new_perturbation = 0 # Perturbation doesn't apply if we are nulling due to failure
            
            processed.append({
                'clip_id': clip_id,
                'label': new_label,
                'reason': new_reason,
                'confidence_score': new_confidence,
                'perturbation_type': new_perturbation
            })
            
            # Add to excluded list
            excluded.append({
                'clip_id': clip_id,
                'reason': new_reason,
                'confidence_score': new_confidence
            })
        else:
            # Keep as is
            processed.append(row)
            
    return processed, excluded

def save_labels_csv(labels: list, filepath: str):
    """Save the processed labels to a CSV file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LABELS_COLUMNS)
        writer.writeheader()
        writer.writerows(labels)
    logger.info(f"Saved {len(labels)} labels to {filepath}")

def save_excluded_log(excluded: list, filepath: str):
    """Save the excluded samples log to a CSV file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure the file exists even if empty
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=EXCLUDED_COLUMNS)
        writer.writeheader()
        if excluded:
            writer.writerows(excluded)
    
    logger.info(f"Saved {len(excluded)} excluded samples to {filepath}")

def save_metadata(metadata: dict, filepath: str):
    """Save metadata JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {filepath}")

def main():
    """Main entry point for applying null labels."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    data_processed_dir = project_root / "data" / "processed"
    
    input_path = data_processed_dir / "labels_raw.csv"
    output_labels_path = data_processed_dir / "labels.csv"
    output_excluded_path = data_processed_dir / "excluded_samples.log"
    metadata_path = data_processed_dir / "null_labels_metadata.json"
    
    logger.info(f"Starting null label application. Input: {input_path}")
    
    try:
        # Load temporary labels
        temp_labels = load_temp_labels(str(input_path))
        logger.info(f"Loaded {len(temp_labels)} temporary labels.")
        
        # Process labels and identify exclusions
        processed_labels, excluded_samples = process_labels_and_exclusions(temp_labels)
        
        # Save outputs
        save_labels_csv(processed_labels, str(output_labels_path))
        save_excluded_log(excluded_samples, str(output_excluded_path))
        
        # Generate metadata
        metadata = {
            "total_samples": len(temp_labels),
            "processed_samples": len(processed_labels),
            "excluded_samples_count": len(excluded_samples),
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "output_labels_file": str(output_labels_path),
            "output_excluded_file": str(output_excluded_path)
        }
        save_metadata(metadata, str(metadata_path))
        
        logger.info("Null label application completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
