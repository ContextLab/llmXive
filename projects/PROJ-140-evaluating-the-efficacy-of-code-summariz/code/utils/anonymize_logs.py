import os
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def setup_logger():
    """Initialize the anonymization logger."""
    return logger

def load_raw_logs(log_path: str) -> List[Dict]:
    """
    Load raw interaction logs from a CSV file.
    
    Args:
        log_path: Path to the raw logs CSV file
    
    Returns:
        List of log entries as dictionaries
    """
    logs = []
    path = Path(log_path)
    
    if not path.exists():
        logger.error(f"Raw log file not found: {log_path}. Cannot proceed with anonymization.")
        raise FileNotFoundError(f"Raw log file not found: {log_path}")
    
    try:
        with open(path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    except Exception as e:
        logger.error(f"Error loading raw logs from {log_path}: {e}")
        raise
    
    return logs

def create_anonymization_mapping(raw_logs: List[Dict], seed: int = 42) -> Dict[str, str]:
    """
    Create a mapping from real participant IDs to anonymized IDs.
    
    Args:
        raw_logs: List of raw log entries
        seed: Random seed for reproducibility (not used here, hashing is deterministic)
    
    Returns:
        Dictionary mapping real participant IDs to anonymized IDs
    """
    unique_participants = list(set(log['participant_id'] for log in raw_logs))
    mapping = {}
    
    for pid in unique_participants:
        # Create a deterministic hash-based anonymized ID
        # Using SHA-256 ensures uniqueness and irreversibility (without the salt)
        hash_obj = hashlib.sha256(pid.encode('utf-8'))
        anon_id = f"ANON_{hash_obj.hexdigest()[:8].upper()}"
        mapping[pid] = anon_id
    
    return mapping

def anonymize_logs(raw_logs: List[Dict], mapping: Dict[str, str]) -> List[Dict]:
    """
    Anonymize participant IDs in the log entries.
    
    Args:
        raw_logs: List of raw log entries
        mapping: Dictionary mapping real IDs to anonymized IDs
    
    Returns:
        List of anonymized log entries
    """
    anonymized = []
    
    for log in raw_logs:
        anon_log = log.copy()
        if 'participant_id' in anon_log and anon_log['participant_id'] in mapping:
            anon_log['participant_id'] = mapping[anon_log['participant_id']]
        # Ensure no other PII fields exist (future-proofing)
        # Currently, the schema only has participant_id as PII
        anonymized.append(anon_log)
    
    return anonymized

def save_anonymized_logs(anonymized_logs: List[Dict], output_path: str) -> None:
    """
    Save anonymized logs to a CSV file.
    
    Args:
        anonymized_logs: List of anonymized log entries
        output_path: Path to the output CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not anonymized_logs:
        logger.warning("No anonymized logs to save.")
        return
    
    fieldnames = [
        'participant_id', 'task_id', 'condition', 'timestamp_ms', 
        'selected_line', 'ground_truth_line'
    ]
    
    try:
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(anonymized_logs)
        logger.info(f"Saved {len(anonymized_logs)} anonymized logs to {output_path}")
    except Exception as e:
        logger.error(f"Error saving anonymized logs to {output_path}: {e}")
        raise

def save_anonymization_mapping(mapping: Dict[str, str], output_path: str) -> None:
    """
    Save the anonymization mapping to a JSON file (for authorized access only).
    
    Args:
        mapping: Dictionary mapping real IDs to anonymized IDs
        output_path: Path to the output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(path, 'w') as f:
            json.dump(mapping, f, indent=2)
        logger.info(f"Saved anonymization mapping to {output_path}")
    except Exception as e:
        logger.error(f"Error saving anonymization mapping to {output_path}: {e}")
        raise

def main():
    """
    Main function to anonymize interaction logs.
    Reads from data/interaction_logs/raw_logs.csv and writes to data/interaction_logs/anonymized_logs.csv.
    """
    # Configuration paths relative to project root
    raw_logs_path = "data/interaction_logs/raw_logs.csv"
    anonymized_logs_path = "data/interaction_logs/anonymized_logs.csv"
    mapping_path = "data/interaction_logs/anonymization_mapping.json"
    
    logger.info(f"Starting anonymization process.")
    logger.info(f"Reading raw logs from: {raw_logs_path}")
    
    try:
        raw_logs = load_raw_logs(raw_logs_path)
    except FileNotFoundError:
        logger.error("Aborting: Raw logs file missing.")
        return 1
    
    if not raw_logs:
        logger.warning("No raw logs found. Skipping anonymization.")
        return 0
    
    logger.info(f"Loaded {len(raw_logs)} raw log entries.")
    
    mapping = create_anonymization_mapping(raw_logs)
    logger.info(f"Created anonymization mapping for {len(mapping)} participants.")
    
    anonymized_logs = anonymize_logs(raw_logs, mapping)
    
    save_anonymized_logs(anonymized_logs, anonymized_logs_path)
    save_anonymization_mapping(mapping, mapping_path)
    
    print(f"Anonymized {len(anonymized_logs)} logs.")
    print(f"Saved anonymized logs to: {anonymized_logs_path}")
    print(f"Saved mapping to: {mapping_path}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
