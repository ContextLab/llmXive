import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
METADATA_DIR = DATA_DIR / "metadata"
EXCLUSION_LOG = METADATA_DIR / "exclusion_log.txt"
SUBJECT_STATUS_FILE = METADATA_DIR / "subject_status.csv"
SUBJECT_LABELS_FILE = METADATA_DIR / "subject_labels.csv"
ANALYSIS_CONFIG_FILE = METADATA_DIR / "analysis_config.json"

def load_exclusion_log() -> List[Dict[str, str]]:
    """
    Load the exclusion log file.
    
    Returns:
        List of dictionaries containing exclusion information
    """
    if not EXCLUSION_LOG.exists():
        logger.warning(f"Exclusion log not found: {EXCLUSION_LOG}")
        return []
    
    excluded_subjects = []
    with open(EXCLUSION_LOG, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            excluded_subjects.append(row)
    
    return excluded_subjects

def load_subject_status() -> Dict[str, str]:
    """
    Load the subject status file.
    
    Returns:
        Dictionary mapping subject_id to status
    """
    if not SUBJECT_STATUS_FILE.exists():
        logger.warning(f"Subject status file not found: {SUBJECT_STATUS_FILE}")
        return {}
    
    status_dict = {}
    with open(SUBJECT_STATUS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            status_dict[row['subject_id']] = row['status']
    
    return status_dict

def parse_diagnostic_label(label: str) -> Optional[str]:
    """
    Parse and validate diagnostic label.
    
    Args:
        label: Raw diagnostic label string
        
    Returns:
        Standardized label ('Schizophrenia', 'Control', or None if invalid)
    """
    label = label.strip().lower()
    
    if label in ['schizophrenia', 'schizophrenic', 'patient', 'case']:
        return 'Schizophrenia'
    elif label in ['control', 'healthy', 'normal', 'hc']:
        return 'Control'
    else:
        logger.warning(f"Invalid diagnostic label: {label}")
        return None

def get_diagnostic_labels_from_participants(dataset_path: str) -> Dict[str, str]:
    """
    Extract diagnostic labels from participants.tsv file.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        Dictionary mapping subject_id to diagnostic label
    """
    participants_file = Path(dataset_path) / "participants.tsv"
    
    if not participants_file.exists():
        logger.error(f"participants.tsv not found in {dataset_path}")
        return {}
    
    try:
        df = pd.read_csv(participants_file, sep='\t')
        
        # Look for common label columns
        label_columns = ['diagnosis', 'group', 'condition', 'patient_status', 'label']
        label_col = None
        
        for col in label_columns:
            if col in df.columns:
                label_col = col
                break
        
        if label_col is None:
            logger.error("No diagnostic label column found in participants.tsv")
            return {}
        
        label_mapping = {}
        for _, row in df.iterrows():
            subject_id = row.get('participant_id', f"sub-{row.name}")
            raw_label = str(row[label_col])
            standardized_label = parse_diagnostic_label(raw_label)
            
            if standardized_label:
                label_mapping[subject_id] = standardized_label
            else:
                logger.warning(f"Could not parse label for {subject_id}: {raw_label}")
        
        return label_mapping
    
    except Exception as e:
        logger.error(f"Error reading participants.tsv: {e}")
        return {}

def generate_subject_labels_mapping(dataset_path: str, exclusion_log: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """
    Generate a comprehensive mapping of subject labels including diagnostic status and inclusion status.
    
    Args:
        dataset_path: Path to the dataset directory
        exclusion_log: List of excluded subjects from the exclusion log
        
    Returns:
        Dictionary mapping subject_id to their metadata
    """
    # Get diagnostic labels
    diagnostic_labels = get_diagnostic_labels_from_participants(dataset_path)
    
    # Create exclusion set
    excluded_subjects = {item['subject_id'] for item in exclusion_log if 'subject_id' in item}
    
    # Build mapping
    subject_mapping = {}
    
    for subject_id, diagnosis in diagnostic_labels.items():
        if subject_id in excluded_subjects:
            status = 'excluded'
            reason = 'Excluded due to metadata issues'
        else:
            status = 'included'
            reason = 'Included in analysis'
        
        subject_mapping[subject_id] = {
            'subject_id': subject_id,
            'diagnosis': diagnosis,
            'status': status,
            'reason': reason
        }
    
    return subject_mapping

def save_subject_labels(subject_mapping: Dict[str, Dict[str, str]], output_file: Optional[str] = None) -> str:
    """
    Save subject labels to CSV file.
    
    Args:
        subject_mapping: Dictionary of subject metadata
        output_file: Optional custom output file path
        
    Returns:
        Path to the saved file
    """
    if output_file is None:
        output_file = str(SUBJECT_LABELS_FILE)
    
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(list(subject_mapping.values()))
    df = df[['subject_id', 'diagnosis', 'status']]
    df.to_csv(output_file, index=False)
    
    logger.info(f"Saved subject labels to {output_file}")
    return output_file

def check_medication_status_available(dataset_path: str) -> bool:
    """
    Check if medication status information is available in the dataset.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        True if medication status is available, False otherwise
    """
    participants_file = Path(dataset_path) / "participants.tsv"
    
    if not participants_file.exists():
        return False
    
    try:
        df = pd.read_csv(participants_file, sep='\t')
        medication_columns = ['medication', 'medication_status', 'meds', 'drug', 'medication_type']
        
        for col in medication_columns:
            if col in df.columns:
                logger.info(f"Found medication column: {col}")
                return True
        
        # Also check for any column containing 'med' in the name
        med_cols = [col for col in df.columns if 'med' in col.lower()]
        if med_cols:
            logger.info(f"Found medication-related columns: {med_cols}")
            return True
        
        return False
    
    except Exception as e:
        logger.warning(f"Could not check medication status: {e}")
        return False

def save_analysis_config(medication_available: bool) -> None:
    """
    Save analysis configuration to JSON file.
    
    Args:
        medication_available: Boolean indicating if medication status is available
    """
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    config = {
        "medication_status_available": medication_available
    }
    
    with open(ANALYSIS_CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Saved analysis config to {ANALYSIS_CONFIG_FILE}")

def run_metadata_pipeline(dataset_path: str) -> Dict[str, str]:
    """
    Run the complete metadata pipeline.
    
    Args:
        dataset_path: Path to the dataset directory
        
    Returns:
        Dictionary of subject labels
    """
    logger.info("Starting metadata pipeline")
    
    # Load exclusion log
    exclusion_log = load_exclusion_log()
    logger.info(f"Loaded {len(exclusion_log)} excluded subjects")
    
    # Generate subject labels mapping
    subject_mapping = generate_subject_labels_mapping(dataset_path, exclusion_log)
    logger.info(f"Generated labels for {len(subject_mapping)} subjects")
    
    # Save subject labels
    save_subject_labels(subject_mapping)
    
    # Check and save medication status availability
    medication_available = check_medication_status_available(dataset_path)
    save_analysis_config(medication_available)
    
    logger.info("Metadata pipeline completed")
    return subject_mapping

def main():
    """Main entry point for the metadata module."""
    logger.info("Metadata module loaded and ready")
    
    # Example usage (would be called by main orchestrator)
    # dataset_path = "data/raw/ds000030"
    # if os.path.exists(dataset_path):
    #     run_metadata_pipeline(dataset_path)

if __name__ == "__main__":
    main()
