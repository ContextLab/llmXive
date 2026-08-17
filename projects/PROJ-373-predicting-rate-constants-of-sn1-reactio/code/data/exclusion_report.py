import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Constants
DATA_CONFIG = DataConfig()

def setup_exclusion_logging() -> logging.Logger:
    """Setup logging for the exclusion report stage."""
    logger = get_logger("exclusion_report")
    logger.setLevel(logging.INFO)
    return logger

def load_exclusion_logs(clean_log_path: Path, descriptor_log_path: Path) -> List[Dict[str, Any]]:
    """
    Load exclusion logs from multiple sources.
    Returns a list of exclusion records.
    """
    exclusions = []
    
    # Load from clean.log
    if clean_log_path.exists():
        with open(clean_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        exclusions.append(record)
                    except json.JSONDecodeError:
                        # If not JSON, treat as raw log line
                        exclusions.append({
                            "row_index": -1,
                            "reason": line,
                            "original_smiles": "unknown"
                        })
    
    # Load from descriptor.log (or exclusion_raw.log)
    if descriptor_log_path.exists():
        with open(descriptor_log_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        exclusions.append(record)
                    except json.JSONDecodeError:
                        exclusions.append({
                            "row_index": -1,
                            "reason": line,
                            "original_smiles": "unknown"
                        })
    
    return exclusions

def map_error_reason(reason: str) -> str:
    """Map error reason strings to schema codes."""
    reason_lower = reason.lower()
    
    if "primary" in reason_lower:
        return "primary_substrate_filter"
    elif "stereo" in reason_lower or "ambiguous" in reason_lower:
        return "ambiguous_stereochemistry"
    elif "missing" in reason_lower or "nan" in reason_lower:
        return "missing_value"
    elif "invalid" in reason_lower or "parse" in reason_lower:
        return "invalid_smiles"
    elif "descriptor" in reason_lower or "charge" in reason_lower:
        return "descriptor_calculation_failed"
    else:
        return "other"

def validate_against_schema(exclusions: List[Dict[str, Any]], schema_path: Path) -> bool:
    """
    Validate exclusion records against the schema.
    Returns True if valid, False otherwise.
    """
    # Load schema
    if not schema_path.exists():
        logging.warning(f"Schema file not found: {schema_path}, skipping validation")
        return True
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)
    
    required_fields = schema.get("required_fields", ["row_index", "reason", "original_smiles"])
    
    for i, exclusion in enumerate(exclusions):
        for field in required_fields:
            if field not in exclusion:
                logging.error(f"Exclusion record {i} missing required field: {field}")
                return False
    
    return True

def generate_exclusion_report(exclusions: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate the final exclusion report CSV."""
    if not exclusions:
        # Create an empty report with headers
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["row_index", "reason", "original_smiles", "error_code"])
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["row_index", "reason", "original_smiles", "error_code"])
        
        for exclusion in exclusions:
            row_index = exclusion.get("row_index", -1)
            reason = exclusion.get("reason", "unknown")
            original_smiles = exclusion.get("original_smiles", "unknown")
            error_code = map_error_reason(reason)
            
            writer.writerow([row_index, reason, original_smiles, error_code])

def main():
    """Main entry point for the exclusion report stage."""
    parser = argparse.ArgumentParser(description="Generate exclusion report from pipeline logs")
    parser.add_argument("--clean-log", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "clean.log"),
                      help="Path to the clean log file")
    parser.add_argument("--descriptor-log", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "exclusion_raw.log"),
                      help="Path to the descriptor exclusion log file")
    parser.add_argument("--schema", type=str, default=str(DATA_CONFIG.CONTRACTS_DIR / "exclusion_report.schema.yaml"),
                      help="Path to the exclusion report schema file")
    parser.add_argument("--output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "exclusion_report.csv"),
                      help="Path to save the exclusion report")
    
    args = parser.parse_args()
    
    logger = setup_exclusion_logging()
    logger.info("Starting exclusion report stage")
    
    try:
        # Ensure directories exist
        ensure_dirs(DATA_CONFIG)
        
        clean_log_path = Path(args.clean_log)
        descriptor_log_path = Path(args.descriptor_log)
        schema_path = Path(args.schema)
        output_path = Path(args.output)
        
        # Load exclusion logs
        logger.info(f"Loading exclusion logs from {clean_log_path} and {descriptor_log_path}")
        exclusions = load_exclusion_logs(clean_log_path, descriptor_log_path)
        logger.info(f"Loaded {len(exclusions)} exclusion records")
        
        # Validate against schema
        logger.info("Validating against schema")
        is_valid = validate_against_schema(exclusions, schema_path)
        if not is_valid:
            logger.warning("Exclusion records failed schema validation")
        
        # Generate exclusion report
        logger.info(f"Generating exclusion report at {output_path}")
        generate_exclusion_report(exclusions, output_path)
        
        logger.info("Exclusion report stage completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during exclusion report stage: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
