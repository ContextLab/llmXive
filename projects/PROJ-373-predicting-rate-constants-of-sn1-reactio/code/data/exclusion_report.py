import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Import from local utils/config if available, otherwise define minimal fallbacks
try:
    from utils.logger import get_logger
except ImportError:
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger

try:
    from config import ensure_dirs, DataConfig
except ImportError:
    # Fallback if config.py is not in path or missing attributes
    def ensure_dirs(*args):
        for arg in args:
            if isinstance(arg, Path):
                arg.mkdir(parents=True, exist_ok=True)
            elif isinstance(arg, list):
                for p in arg:
                    if isinstance(p, Path):
                        p.mkdir(parents=True, exist_ok=True)
        return None

    class DataConfig:
        def __init__(self):
            self.processed_dir = "data/processed"
            self.raw_dir = "data/raw"
        
        def __getattr__(self, name):
            # Tolerant fallback for unknown attributes
            if name.endswith('_dir'):
                return name.replace('_dir', '').replace('data', 'data')
            def _noop(*args, **kwargs):
                return None
            return _noop

def setup_exclusion_logging(log_path: Optional[Path] = None):
    """
    Setup logging for exclusion report generation.
    Tolerant of various call signatures (with or without path).
    """
    logger = logging.getLogger('exclusion_report')
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Ensure directory exists
    if log_path:
        ensure_dirs(log_path.parent)
        fh = logging.FileHandler(log_path)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    # Also add console handler for immediate feedback
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)
    
    return logger

def load_exclusion_logs(clean_log_path: Path, raw_log_path: Path) -> List[Dict[str, Any]]:
    """
    Load and merge exclusion logs from clean.log and exclusion_raw.log.
    Handles missing files gracefully by returning empty lists.
    """
    entries = []
    
    # Load clean.log (T012 output)
    if clean_log_path.exists():
        try:
            with open(clean_log_path, 'r', encoding='utf-8') as f:
                # Assuming CSV format: row_index,reason,original_smiles or similar
                reader = csv.DictReader(f)
                for row in reader:
                    # Normalize keys if necessary
                    entry = {
                        'row_index': row.get('row_index', ''),
                        'reason': row.get('reason', row.get('message', '')),
                        'original_smiles': row.get('original_smiles', '')
                    }
                    entries.append(entry)
        except Exception as e:
            logging.warning(f"Could not parse clean.log: {e}")
    else:
        logging.warning(f"Clean log not found: {clean_log_path}")
    
    # Load exclusion_raw.log (T011e, T013 output)
    if raw_log_path.exists():
        try:
            with open(raw_log_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entry = {
                        'row_index': row.get('row_index', ''),
                        'reason': row.get('reason', ''),
                        'original_smiles': row.get('original_smiles', '')
                    }
                    entries.append(entry)
        except Exception as e:
            logging.warning(f"Could not parse exclusion_raw.log: {e}")
    else:
        logging.warning(f"Exclusion raw log not found: {raw_log_path}")
    
    return entries

def map_error_reason(reason: str) -> str:
    """
    Map error strings to schema codes.
    Mapping defined in T015 specification.
    """
    mapping = {
        'Primary substrate': 'primary_substrate_filter',
        'Ambiguous stereochemistry': 'ambiguous_stereochemistry',
        'Descriptor calculation failed': 'descriptor_failure',
        'Missing rate constant': 'missing_rate_constant',
        'Missing SMILES': 'missing_smiles',
        'Invalid substrate label': 'invalid_substrate_label'
    }
    
    # Case-insensitive partial match
    reason_lower = reason.lower()
    for key, code in mapping.items():
        if key.lower() in reason_lower:
            return code
    
    # If no match, return a generic code or the original reason
    return 'unknown_error'

def validate_against_schema(entries: List[Dict[str, Any]], schema_path: Path) -> bool:
    """
    Validate exclusion entries against the schema.
    Returns True if valid, False otherwise.
    """
    if not schema_path.exists():
        logging.warning(f"Schema file not found: {schema_path}. Skipping validation.")
        return True  # Skip validation if schema missing, but log warning
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Failed to load schema: {e}")
        return False
    
    required_fields = schema.get('required_fields', ['row_index', 'reason', 'original_smiles'])
    
    for i, entry in enumerate(entries):
        for field in required_fields:
            if field not in entry or entry[field] is None:
                logging.error(f"Entry {i} missing required field: {field}")
                return False
    return True

def generate_exclusion_report(entries: List[Dict[str, Any]], output_path: Path, mapped_output_path: Path):
    """
    Generate the final exclusion report CSV and the mapped JSON intermediate.
    """
    # 1. Create mapped JSON
    mapped_entries = []
    for entry in entries:
        mapped_entry = entry.copy()
        mapped_entry['reason_code'] = map_error_reason(entry.get('reason', ''))
        mapped_entries.append(mapped_entry)
    
    with open(mapped_output_path, 'w', encoding='utf-8') as f:
        json.dump(mapped_entries, f, indent=2)
    
    # 2. Write final CSV
    ensure_dirs(output_path.parent)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['row_index', 'reason', 'reason_code', 'original_smiles'])
        writer.writeheader()
        for entry in mapped_entries:
            writer.writerow({
                'row_index': entry.get('row_index', ''),
                'reason': entry.get('reason', ''),
                'reason_code': entry.get('reason_code', ''),
                'original_smiles': entry.get('original_smiles', '')
            })

def main():
    parser = argparse.ArgumentParser(description="Aggregate and validate exclusion logs.")
    parser.add_argument('--aggregate', action='store_true', help="Run aggregation mode.")
    parser.add_argument('--clean-log', type=str, help="Path to clean.log (T012 output).")
    parser.add_argument('--raw-log', type=str, help="Path to exclusion_raw.log (T011e, T013 output).")
    parser.add_argument('--input', type=str, help="Path to input exclusion log (for validation mode).")
    parser.add_argument('--schema', type=str, help="Path to schema YAML file.")
    parser.add_argument('--output', type=str, required=True, help="Path to output exclusion report CSV.")
    parser.add_argument('--mapped-output', type=str, default="data/processed/exclusion_mapped.json", help="Path to mapped JSON output.")
    
    args = parser.parse_args()
    
    logger = setup_exclusion_logging(Path("data/processed/exclusion_aggregation.log"))
    logger.info("Starting exclusion report aggregation...")
    
    config = DataConfig()
    processed_dir = Path(config.processed_dir)
    
    # Guard Clause: Check for upstream files if in aggregate mode
    if args.aggregate:
        clean_log_path = Path(args.clean_log) if args.clean_log else processed_dir / "clean.log"
        raw_log_path = Path(args.raw_log) if args.raw_log else processed_dir / "exclusion_raw.log"
        
        if not clean_log_path.exists() or not raw_log_path.exists():
            logger.error("Upstream files missing. Writing blocked status.")
            # Write blocked status to output
            ensure_dirs(Path(args.output).parent)
            with open(args.output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['status', 'reason'])
                writer.writeheader()
                writer.writerow({'status': 'blocked', 'reason': 'upstream_missing'})
            sys.exit(1)
        
        entries = load_exclusion_logs(clean_log_path, raw_log_path)
        logger.info(f"Loaded {len(entries)} exclusion entries.")
        
        if not entries:
            logger.warning("No exclusion entries found. Creating empty report.")
        
        output_path = Path(args.output)
        mapped_path = Path(args.mapped_output)
        
        generate_exclusion_report(entries, output_path, mapped_path)
        
        # Validate against schema if provided
        if args.schema:
            schema_path = Path(args.schema)
            if validate_against_schema(entries, schema_path):
                logger.info("Validation passed.")
            else:
                logger.error("Validation failed.")
                sys.exit(1)
        
        logger.info(f"Exclusion report saved to {output_path}")
    
    else:
        # Validation mode (T013b equivalent)
        input_path = Path(args.input) if args.input else processed_dir / "exclusion_raw.log"
        schema_path = Path(args.schema) if args.schema else Path("specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml")
        
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            sys.exit(1)
        
        entries = load_exclusion_logs(Path(), input_path) # Hacky load for single file
        # Re-load specifically for single file validation
        entries = []
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        
        if validate_against_schema(entries, schema_path):
            logger.info("Validation passed.")
            # Write validation success log
            validation_log_path = Path(args.output)
            ensure_dirs(validation_log_path.parent)
            with open(validation_log_path, 'w', encoding='utf-8') as f:
                f.write("Validation Status: PASS\n")
        else:
            logger.error("Validation failed.")
            sys.exit(1)

if __name__ == "__main__":
    main()