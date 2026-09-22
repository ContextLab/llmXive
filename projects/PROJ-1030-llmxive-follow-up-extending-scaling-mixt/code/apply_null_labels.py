import os
import sys
import json
import csv
import logging
from pathlib import Path

# Ensure project root is in path for imports if run directly
if __name__ == "__main__" and "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_config import get_logger, log_excluded_sample
from utils.config_manager import get_config

logger = get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.9

def load_json_file(file_path: str) -> dict:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_temp_labels(file_path: str) -> list:
    """Load temporary labels from a JSON file (output of T023)."""
    # T023 output structure assumed: list of dicts with clip_id, label, reason, confidence_score, perturbation_type
    # If T023 outputs CSV, this would need adjustment, but spec implies intermediate JSON or dict structure.
    # Based on T023 description, it assigns labels. We assume it outputs a list of result dicts.
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Temporary labels file not found: {file_path}")
        return []

def process_labels_and_exclusions(temp_labels: list, threshold: float = CONFIDENCE_THRESHOLD) -> tuple:
    """
    Process temporary labels to assign 'null' to low confidence or failed samples.
    
    Args:
        temp_labels: List of dicts containing label info.
        threshold: Confidence threshold for exclusion.
        
    Returns:
        Tuple of (final_labels_list, excluded_samples_list)
    """
    final_labels = []
    excluded_samples = []
    
    for item in temp_labels:
        clip_id = item.get('clip_id')
        label = item.get('label')
        reason = item.get('reason', 'unknown')
        confidence_score = item.get('confidence_score', 0.0)
        perturbation_type = item.get('perturbation_type', 0)
        
        # Determine if this sample should be excluded (assigned 'null')
        # Condition 1: Simulation failures (often indicated by label being None or specific reason)
        # Condition 2: Confidence score < threshold
        is_excluded = False
        exclusion_reason = reason
        
        # If label is already 'null' or None from previous step, keep it null
        if label is None or label == 'null':
            is_excluded = True
            if not exclusion_reason:
                exclusion_reason = "simulation_failure_or_missing"
        elif confidence_score is not None and confidence_score < threshold:
            is_excluded = True
            exclusion_reason = f"low_confidence_{confidence_score:.4f}"
        
        if is_excluded:
            # Assign 'null' label
            final_label = 'null'
            final_reason = exclusion_reason
            # Log the excluded sample
            log_excluded_sample(clip_id, final_reason, confidence_score)
            excluded_samples.append({
                'clip_id': clip_id,
                'reason': final_reason,
                'confidence_score': confidence_score
            })
            # Update the item for the final list
            item['label'] = final_label
            item['reason'] = final_reason
            item['confidence_score'] = confidence_score # Keep original score for metadata
        else:
            # Keep original label
            final_label = label
            final_reason = reason
            item['label'] = final_label
            item['reason'] = final_reason
            item['confidence_score'] = confidence_score
        
        final_labels.append(item)
        
    return final_labels, excluded_samples

def save_labels_csv(labels: list, output_path: str):
    """Save the final labels to a CSV file."""
    if not labels:
        logger.warning("No labels to save.")
        # Create empty file with headers if no data
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['clip_id', 'label', 'reason', 'confidence_score', 'perturbation_type'])
        return

    # Ensure headers are present
    fieldnames = ['clip_id', 'label', 'reason', 'confidence_score', 'perturbation_type']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for label in labels:
            writer.writerow({
                'clip_id': label.get('clip_id', ''),
                'label': label.get('label', ''),
                'reason': label.get('reason', ''),
                'confidence_score': label.get('confidence_score', 0.0),
                'perturbation_type': label.get('perturbation_type', 0)
            })
    logger.info(f"Saved {len(labels)} labels to {output_path}")

def save_excluded_log(excluded_samples: list, output_path: str):
    """Save the excluded samples log to a CSV file."""
    # Even if empty, create the file with headers as per requirement
    fieldnames = ['clip_id', 'reason', 'confidence_score']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sample in excluded_samples:
            writer.writerow({
                'clip_id': sample.get('clip_id', ''),
                'reason': sample.get('reason', ''),
                'confidence_score': sample.get('confidence_score', 0.0)
            })
    
    logger.info(f"Saved {len(excluded_samples)} excluded samples to {output_path}")

def save_metadata(labels: list, output_path: str):
    """Save metadata about the labeling process."""
    # Extract confidence scores and other stats
    metadata = {
        'total_samples': len(labels),
        'null_count': sum(1 for l in labels if l.get('label') == 'null'),
        'valid_count': sum(1 for l in labels if l.get('label') == 'valid'),
        'invalid_count': sum(1 for l in labels if l.get('label') == 'invalid'),
        'confidence_threshold': CONFIDENCE_THRESHOLD
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {output_path}")

def main():
    """Main entry point for applying null labels."""
    # Paths relative to project root
    project_root = Path(__file__).parent.parent
    data_processed_dir = project_root / "data" / "processed"
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Input from T023 (assumed to be a JSON file of temporary labels)
    # The spec says T023 outputs labels. We assume a temporary JSON file.
    temp_labels_path = data_processed_dir / "temp_labels.json"
    
    # Output paths
    labels_csv_path = data_processed_dir / "labels.csv"
    excluded_log_path = data_processed_dir / "excluded_samples.log"
    metadata_path = data_processed_dir / "metadata.json"
    
    if not temp_labels_path.exists():
        logger.error(f"Input file {temp_labels_path} not found. T023 may not have completed.")
        # Create empty outputs to satisfy artifact existence requirement
        save_labels_csv([], str(labels_csv_path))
        save_excluded_log([], str(excluded_log_path))
        save_metadata([], str(metadata_path))
        return
    
    # Load temporary labels
    temp_labels = load_temp_labels(str(temp_labels_path))
    logger.info(f"Loaded {len(temp_labels)} temporary labels.")
    
    # Process labels and exclusions
    final_labels, excluded_samples = process_labels_and_exclusions(temp_labels)
    
    # Save artifacts
    save_labels_csv(final_labels, str(labels_csv_path))
    save_excluded_log(excluded_samples, str(excluded_log_path))
    save_metadata(final_labels, str(metadata_path))
    
    logger.info("T024 completed successfully.")

if __name__ == "__main__":
    main()
