import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def load_exclusion_logs(config: DataConfig) -> list:
    """Load exclusion logs from clean.log and descriptor.log."""
    logs = []
    
    # Load clean.log
    clean_log_path = config.processed_data_path / "clean.log"
    if clean_log_path.exists():
        with open(clean_log_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        logs.append(entry)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse clean.log line: {line}")
    
    # Load descriptor.log
    desc_log_path = config.processed_data_path / "descriptor.log"
    if desc_log_path.exists():
        with open(desc_log_path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        logs.append(entry)
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse descriptor.log line: {line}")
    
    logger.info(f"Loaded {len(logs)} exclusion entries.")
    return logs

def map_error_reason(raw_reason: str) -> str:
    """Map raw error strings to schema-compliant codes."""
    mapping = {
        'SMILES canonicalization failed': 'canonicalization_error',
        'Gasteiger convergence error': 'gasteiger_convergence_error',
        'Primary substrate': 'primary_substrate_filter',
        'ambiguous_stereochemistry': 'ambiguous_stereochemistry',
        'Missing rate constant': 'missing_rate_constant',
        'Missing SMILES': 'missing_smiles'
    }
    return mapping.get(raw_reason, 'unclassified')

def validate_against_schema(data: list, schema_path: Path) -> bool:
    """Validate data against the exclusion_report schema."""
    # Simple validation: check required keys
    required_keys = ['row_index', 'reason', 'original_smiles']
    for i, entry in enumerate(data):
        for key in required_keys:
            if key not in entry:
                logger.error(f"Entry {i} missing key: {key}")
                return False
    return True

def generate_exclusion_report(config: DataConfig):
    """Generate the final exclusion report CSV."""
    logs = load_exclusion_logs(config)
    
    mapped_logs = []
    for entry in logs:
        mapped_entry = {
            'row_index': entry.get('row_index', -1),
            'reason': map_error_reason(entry.get('reason', 'unknown')),
            'original_smiles': entry.get('original_smiles', '')
        }
        mapped_logs.append(mapped_entry)
    
    # Validate
    # Note: We don't have the schema path here, assuming basic validation
    if not validate_against_schema(mapped_logs, Path("specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml")):
        logger.warning("Exclusion report validation failed, but proceeding.")
    
    # Save
    output_path = config.processed_data_path / "exclusion_report.csv"
    df = pd.DataFrame(mapped_logs)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved exclusion report to {output_path}")
    return output_path

def main():
    config = DataConfig()
    generate_exclusion_report(config)

if __name__ == "__main__":
    main()