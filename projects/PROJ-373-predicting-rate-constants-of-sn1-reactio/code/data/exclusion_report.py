import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import ensure_dirs, DataConfig
from utils.logger import get_logger

logger = get_logger(__name__)

def setup_exclusion_logging():
    """Setup logging for exclusion report generation."""
    return get_logger(__name__)

def load_exclusion_logs(log_paths: List[str]) -> List[Dict[str, Any]]:
    """Load exclusion logs from multiple files."""
    exclusions = []
    
    for log_path in log_paths:
        if not os.path.exists(log_path):
            logger.warning(f"Exclusion log not found: {log_path}")
            continue
        
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                exclusions.append(row)
    
    return exclusions

def map_error_reason(reason: str) -> str:
    """Map error reason to schema code."""
    mapping = {
        'Primary substrate': 'primary_substrate_filter',
        'Ambiguous stereochemistry': 'ambiguous_stereochemistry',
        'Descriptor calculation failed': 'descriptor_failure',
        'Missing rate constant': 'missing_rate_constant',
        'Missing SMILES': 'missing_smiles',
        'invalid_smiles': 'invalid_smiles',
        'canonicalization_error': 'canonicalization_error',
        'gasteiger_error': 'gasteiger_error',
        'topological_error': 'topological_error',
    }
    return mapping.get(reason, reason)

def validate_against_schema(exclusions: List[Dict[str, Any]], schema_path: str) -> bool:
    """Validate exclusions against schema."""
    # Simple validation: check required fields
    required_fields = ['row_index', 'reason', 'original_smiles']
    
    for exclusion in exclusions:
        for field in required_fields:
            if field not in exclusion:
                logger.error(f"Missing required field '{field}' in exclusion: {exclusion}")
                return False
    
    return True

def generate_exclusion_report(exclusions: List[Dict[str, Any]], output_path: str):
    """Generate final exclusion report."""
    # Map error reasons
    mapped_exclusions = []
    for exclusion in exclusions:
        mapped_exclusion = exclusion.copy()
        mapped_exclusion['reason'] = map_error_reason(exclusion['reason'])
        mapped_exclusions.append(mapped_exclusion)
    
    # Save to CSV
    if mapped_exclusions:
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['row_index', 'reason', 'original_smiles'])
            writer.writeheader()
            writer.writerows(mapped_exclusions)
        logger.info(f"Exclusion report saved to {output_path} with {len(mapped_exclusions)} entries")
    else:
        # Create empty report
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['row_index', 'reason', 'original_smiles'])
            writer.writeheader()
        logger.info(f"Empty exclusion report saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate exclusion report")
    parser.add_argument("--log-paths", nargs='+', default=[
        'data/processed/exclusion_raw.log',
        'data/processed/clean.log'
    ], help="Exclusion log paths")
    parser.add_argument("--output", type=str, default="data/processed/exclusion_report.csv", help="Output file path")
    parser.add_argument("--schema", type=str, default="specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml", help="Schema file path")
    args = parser.parse_args()

    ensure_dirs()
    
    try:
        # Load exclusion logs
        exclusions = load_exclusion_logs(args.log_paths)
        logger.info(f"Loaded {len(exclusions)} exclusions")
        
        # Validate against schema
        if validate_against_schema(exclusions, args.schema):
            logger.info("Exclusions validated against schema")
        else:
            logger.warning("Exclusions failed schema validation")
        
        # Generate report
        generate_exclusion_report(exclusions, args.output)
        
    except Exception as e:
        logger.error(f"Exclusion report generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
