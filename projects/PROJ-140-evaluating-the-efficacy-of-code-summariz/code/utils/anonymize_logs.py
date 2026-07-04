import os
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Import existing utilities from the project
from utils.logging_utils import get_logger, setup_logging
from utils.models import InteractionLog
from utils.config_manager import get_config

logger = None

def setup_logger():
    global logger
    if logger is None:
        setup_logging()
        logger = get_logger("anonymize_logs")

def load_raw_logs(input_path: str) -> List[Dict]:
    """Load raw interaction logs from CSV."""
    setup_logger()
    logger.info(f"Loading raw logs from {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Raw log file not found: {input_path}")
        raise FileNotFoundError(f"Raw log file not found: {input_path}")
    
    logs = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    
    logger.info(f"Loaded {len(logs)} raw log entries")
    return logs

def create_anonymization_mapping(raw_logs: List[Dict], salt: str) -> Dict[str, str]:
    """Create a deterministic mapping from participant_id to anonymized_id."""
    mapping = {}
    
    # Collect unique participant IDs
    participant_ids = sorted(set(log.get('participant_id', '') for log in raw_logs if log.get('participant_id')))
    
    for pid in participant_ids:
        if not pid:
            continue
        # Create deterministic hash with salt
        hash_input = f"{pid}:{salt}"
        hash_val = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12]
        anonymized_id = f"ANON_{hash_val.upper()}"
        mapping[pid] = anonymized_id
        logger.debug(f"Mapped participant {pid} -> {anonymized_id}")
    
    logger.info(f"Created anonymization mapping for {len(mapping)} participants")
    return mapping

def anonymize_logs(raw_logs: List[Dict], mapping: Dict[str, str]) -> List[Dict]:
    """Anonymize participant IDs in log entries."""
    anonymized_logs = []
    
    for log in raw_logs:
        new_log = log.copy()
        original_pid = new_log.get('participant_id', '')
        
        if original_pid in mapping:
            new_log['participant_id'] = mapping[original_pid]
        else:
            # If participant_id not in mapping, generate one on the fly (edge case)
            logger.warning(f"Participant ID {original_pid} not in mapping, generating on-the-fly")
            hash_input = f"{original_pid}:ON_THE_FLY"
            hash_val = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:12]
            new_log['participant_id'] = f"ANON_{hash_val.upper()}"
        
        anonymized_logs.append(new_log)
    
    logger.info(f"Anonymized {len(anonymized_logs)} log entries")
    return anonymized_logs

def save_anonymized_logs(logs: List[Dict], output_path: str):
    """Save anonymized logs to CSV."""
    setup_logger()
    
    if not logs:
        logger.warning("No logs to save")
        return
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    fieldnames = list(logs[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(logs)
    
    logger.info(f"Saved anonymized logs to {output_path}")

def save_anonymization_mapping(mapping: Dict[str, str], output_path: str, config_path: str):
    """Save the anonymization mapping to a secure JSON file."""
    setup_logger()
    
    if not mapping:
        logger.warning("No mapping to save")
        return
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Add metadata
    mapping_data = {
        "created_at": datetime.utcnow().isoformat(),
        "salt_used": True,  # We don't store the salt itself for security
        "mapping": mapping,
        "note": "This file contains the anonymization key. Keep it secure and separate from anonymized data."
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping_data, f, indent=2)
    
    # Set restrictive permissions (600 = owner read/write only)
    try:
        os.chmod(output_path, 0o600)
        logger.info(f"Set restrictive permissions on mapping file: {output_path}")
    except OSError as e:
        logger.warning(f"Could not set permissions on {output_path}: {e}")
    
    logger.info(f"Saved anonymization mapping to {output_path}")

def main():
    """Main entry point for anonymization script."""
    setup_logger()
    logger.info("Starting log anonymization process")
    
    config = get_config()
    
    # Get paths from config or use defaults
    raw_logs_path = config.get('paths', {}).get('raw_interaction_logs', 'data/interaction_logs/raw_logs.csv')
    anonymized_logs_path = config.get('paths', {}).get('anonymized_interaction_logs', 'data/interaction_logs/anonymized_logs.csv')
    mapping_path = config.get('paths', {}).get('anonymization_mapping', 'data/interaction_logs/anonymization_mapping.json')
    salt = config.get('anonymization', {}).get('salt', 'PROJ-140-default-salt')
    
    logger.info(f"Configuration: raw_logs={raw_logs_path}, output={anonymized_logs_path}")
    
    try:
        # Step 1: Load raw logs
        raw_logs = load_raw_logs(raw_logs_path)
        
        # Step 2: Create anonymization mapping
        mapping = create_anonymization_mapping(raw_logs, salt)
        
        # Step 3: Anonymize logs
        anonymized_logs = anonymize_logs(raw_logs, mapping)
        
        # Step 4: Save anonymized logs
        save_anonymized_logs(anonymized_logs, anonymized_logs_path)
        
        # Step 5: Save mapping (securely)
        save_anonymization_mapping(mapping, mapping_path, config.get('config_path', '.env'))
        
        logger.info("Anonymization completed successfully")
        print(f"Anonymized logs saved to: {anonymized_logs_path}")
        print(f"Mapping saved to: {mapping_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        raise

if __name__ == "__main__":
    main()
