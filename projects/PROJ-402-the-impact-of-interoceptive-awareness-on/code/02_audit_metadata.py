import os
import sys
import json
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils.schema_validator import load_schema_from_file, validate_file_against_schema, SchemaValidationError, FileLoadError
from utils.bids_scanner import find_events_files, scan_events_for_tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
DATA_RAW_DIR = Path("data/raw")
RESULTS_DIR = Path("results")

def load_schema():
    """Load schema from file."""
    logger.info(f"Loading schema from {SCHEMA_PATH}")
    try:
        schema = load_schema_from_file(SCHEMA_PATH)
        logger.info("Schema loaded successfully")
        return schema
    except FileLoadError as e:
        logger.error(f"Failed to load schema: {e}")
        raise

def validate_events_tsv(events_file_path: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a single events.tsv file against the schema.
    
    Returns a dict with:
      - 'valid': bool
      - 'errors': list of error messages
      - 'file': path string
    """
    result = {
        'valid': True,
        'errors': [],
        'file': str(events_file_path)
    }
    
    if not events_file_path.exists():
        result['valid'] = False
        result['errors'].append(f"File not found: {events_file_path}")
        return result
    
    try:
        # Use the validator from the schema utility
        validation_result = validate_file_against_schema(
            str(events_file_path),
            schema,
            file_type="tsv"
        )
        
        if not validation_result.get('valid', False):
            result['valid'] = False
            result['errors'].extend(validation_result.get('errors', []))
            logger.warning(f"Validation failed for {events_file_path}: {validation_result.get('errors', [])}")
        else:
            logger.info(f"Validation passed for {events_file_path}")
            
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"Validation error: {str(e)}")
        logger.error(f"Unexpected error validating {events_file_path}: {e}")
        
    return result

def remote_metadata_pre_check():
    """Perform remote metadata pre-check."""
    logger.info("Checking remote metadata sources (OpenNeuro index)...")
    index_path = DATA_RAW_DIR / "openneuro" / "index.json"
    
    if not index_path.exists():
        logger.warning("OpenNeuro index not found. Skipping remote check.")
        return {'checked': False, 'reason': 'Index not found'}
    
    try:
        with open(index_path, 'r') as f:
            index_data = json.load(f)
        
        # Look for TSST and heartbeat/interoception keywords
        relevant_studies = []
        for dataset in index_data.get('datasets', []):
            dataset_id = dataset.get('id', '')
            keywords = dataset.get('keywords', [])
            description = dataset.get('description', {}).get('name', '')
            
            combined_text = (description + " " + " ".join(keywords)).lower()
            
            has_tsst = 'tsst' in combined_text
            has_interoception = any(kw in combined_text for kw in ['heartbeat', 'interoception', 'interoceptive'])
            
            if has_tsst and has_interoception:
                relevant_studies.append({
                    'id': dataset_id,
                    'name': description,
                    'keywords': keywords
                })
        
        logger.info(f"Found {len(relevant_studies)} relevant studies in OpenNeuro index")
        return {
            'checked': True,
            'relevant_studies': relevant_studies,
            'count': len(relevant_studies)
        }
        
    except Exception as e:
        logger.error(f"Error checking remote metadata: {e}")
        return {'checked': False, 'reason': str(e)}

def local_bids_scan(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform local BIDS scan for events.tsv files and validate them.
    
    Returns a dict with:
      - 'events_files': list of found files
      - 'validations': list of validation results
      - 'found_tasks': set of found task labels
      - 'feasibility_status': 'Success' or 'Failure'
    """
    logger.info("Starting local BIDS scan...")
    
    events_files = find_events_files(DATA_RAW_DIR)
    logger.info(f"Found {len(events_files)} events.tsv files")
    
    validations = []
    found_tasks = set()
    has_schandry_or_heartbeat = False
    has_tsst = False
    
    for event_file in events_files:
        # Validate against schema
        validation_result = validate_events_tsv(event_file, schema)
        validations.append(validation_result)
        
        if validation_result['valid']:
            # Scan for tasks in valid files
            try:
                import pandas as pd
                df = pd.read_csv(event_file, sep='\t')
                if 'task' in df.columns:
                    tasks = df['task'].unique()
                    for task in tasks:
                        task_lower = str(task).lower()
                        found_tasks.add(task_lower)
                        
                        if task_lower in ['schandry', 'heartbeat']:
                            has_schandry_or_heartbeat = True
                        if task_lower == 'tsst':
                            has_tsst = True
            except Exception as e:
                logger.warning(f"Could not scan tasks from {event_file}: {e}")
    
    # Determine feasibility status
    if has_schandry_or_heartbeat:
        feasibility_status = "Success"
        logger.info("Feasibility Success: Found Schandry or heartbeat task")
    else:
        feasibility_status = "Failure"
        logger.info("Feasibility Failure: Missing behavioral task (Schandry/heartbeat)")
    
    return {
        'events_files': [str(f) for f in events_files],
        'validations': validations,
        'found_tasks': list(found_tasks),
        'has_schandry_or_heartbeat': has_schandry_or_heartbeat,
        'has_tsst': has_tsst,
        'feasibility_status': feasibility_status
    }

def generate_audit_report(remote_check: Dict[str, Any], local_scan: Dict[str, Any]) -> Path:
    """
    Generate the final audit report to results/data_audit.md.
    
    Returns the path to the generated report.
    """
    logger.info("Generating audit report...")
    
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS_DIR / "data_audit.md"
    
    with open(report_path, 'w') as f:
        f.write("# Data Availability Audit Report\n\n")
        f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Remote Check Section
        f.write("## Remote Metadata Check (OpenNeuro)\n")
        if remote_check.get('checked'):
            f.write(f"- **Status:** Checked\n")
            f.write(f"- **Relevant Studies Found:** {remote_check.get('count', 0)}\n")
            if remote_check.get('relevant_studies'):
                f.write("\n### Relevant Studies\n")
                for study in remote_check['relevant_studies']:
                    f.write(f"- **{study['id']}**: {study['name']}\n")
                    f.write(f"  - Keywords: {', '.join(study['keywords'])}\n")
        else:
            f.write(f"- **Status:** Not Checked\n")
            f.write(f"- **Reason:** {remote_check.get('reason', 'Unknown')}\n")
        f.write("\n")
        
        # Local Scan Section
        f.write("## Local BIDS Scan\n")
        f.write(f"- **Events Files Found:** {len(local_scan.get('events_files', []))}\n")
        f.write(f"- **Tasks Found:** {', '.join(local_scan.get('found_tasks', []))}\n")
        f.write(f"- **Has Schandry/Heartbeat:** {local_scan.get('has_schandry_or_heartbeat', False)}\n")
        f.write(f"- **Has TSST:** {local_scan.get('has_tsst', False)}\n")
        f.write("\n")
        
        # Validation Results
        f.write("## Schema Validation Results\n")
        for v in local_scan.get('validations', []):
            status = "✅ Valid" if v['valid'] else "❌ Invalid"
            f.write(f"- **{v['file']}**: {status}\n")
            if v['errors']:
                for err in v['errors']:
                    f.write(f"  - {err}\n")
        f.write("\n")
        
        # Feasibility Status
        f.write("## Feasibility Status\n")
        status = local_scan.get('feasibility_status', 'Unknown')
        if status == "Success":
            f.write("### ✅ Feasibility Success\n")
            f.write("Required behavioral tasks (Schandry/heartbeat) found in local data.\n")
            f.write("Pipeline can proceed to HRV preprocessing (Phase 4).\n")
        else:
            f.write("### ❌ Feasibility Failure: Missing Behavioral Task\n")
            f.write("Required behavioral tasks (Schandry/heartbeat) NOT found in local data.\n")
            f.write("Pipeline will trigger UBDE calculation path (T030).\n")
        
    logger.info(f"Audit report generated at {report_path}")
    return report_path

def main():
    """Main entry point for audit metadata script."""
    start_time = time.time()
    logger.info("Starting metadata audit...")
    
    try:
        # 1. Load Schema
        schema = load_schema()
        
        # 2. Remote Pre-check
        remote_result = remote_metadata_pre_check()
        
        # 3. Local BIDS Scan with Validation
        local_result = local_bids_scan(schema)
        
        # 4. Generate Report
        report_path = generate_audit_report(remote_result, local_result)
        
        elapsed = time.time() - start_time
        logger.info(f"Audit completed in {elapsed:.2f} seconds")
        logger.info(f"Report saved to: {report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
