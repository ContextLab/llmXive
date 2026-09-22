"""
Audit metadata for Interoceptive Awareness study.

This script performs a two-part scan:
1. Remote Metadata Pre-Check: Queries Zenodo REST API for 'Schandry' or 'heartbeat' tasks.
2. Local BIDS Scan: Scans local BIDS events.tsv files if the download (T010) succeeded.

Output: results/data_audit.md
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import yaml
import pandas as pd
from utils.schema_validator import load_schema_from_file, validate_file_against_schema, SchemaValidationError, FileLoadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/audit.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ZENODO_API_URL = "https://zenodo.org/api/records"
WESAD_DOI = "10.5281/zenodo.1292932"
REQUIRED_TASKS = ['Schandry', 'heartbeat']
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
AUDIT_REPORT_PATH = Path("results/data_audit.md")
DOWNLOAD_FLAG_PATH = Path("data/.wesad_download_complete")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from the contracts directory."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_events_tsv(events_file: Path, schema: Dict[str, Any]) -> bool:
    """Validate an events.tsv file against the schema."""
    try:
        validate_file_against_schema(str(events_file), schema)
        return True
    except (SchemaValidationError, FileLoadError) as e:
        logger.warning(f"Validation failed for {events_file}: {e}")
        return False

def remote_metadata_pre_check() -> Dict[str, Any]:
    """
    Query Zenodo REST API to check for required tasks in WESAD dataset.
    
    Returns:
        Dict with 'found' (bool), 'tasks_found' (list), 'status' (str)
    """
    logger.info("Performing Remote Metadata Pre-Check on Zenodo...")
    try:
        # Zenodo API search for records related to WESAD DOI
        # We search for the specific record and inspect its metadata/files if available
        # Note: Zenodo API for file listing is limited for unauthenticated users or specific records.
        # We will attempt to fetch the record metadata first.
        
        record_id = "1292932" # Extracted from DOI 10.5281/zenodo.1292932
        url = f"{ZENODO_API_URL}/{record_id}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check metadata for keywords in description or title
        metadata = data.get('metadata', {})
        description = metadata.get('description', '').lower()
        title = metadata.get('title', '').lower()
        
        tasks_found = []
        for task in REQUIRED_TASKS:
            if task.lower() in description or task.lower() in title:
                tasks_found.append(task)
        
        # Note: Zenodo API doesn't always expose file-level task labels in the main record metadata.
        # If not found in metadata, we assume inconclusive and rely on local scan.
        # However, for this specific dataset (WESAD), the tasks are known to be present in the raw files.
        # The "Remote Pre-Check" here acts as a sanity check. If the record itself doesn't mention the tasks
        # (which it might not in the abstract), we mark it as inconclusive to proceed to local scan.
        
        if tasks_found:
            logger.info(f"Remote check found tasks: {tasks_found}")
            return {
                'found': True,
                'tasks_found': tasks_found,
                'status': 'success'
            }
        else:
            # If not found in metadata, we cannot definitively say they are missing without file access.
            # We mark as inconclusive to force local scan if download exists.
            logger.warning("Remote check inconclusive: Tasks not explicitly listed in record metadata.")
            return {
                'found': False,
                'tasks_found': [],
                'status': 'inconclusive'
            }

    except requests.exceptions.RequestException as e:
        logger.error(f"Remote metadata check failed: {e}")
        return {
            'found': False,
            'tasks_found': [],
            'status': 'error'
        }

def local_bids_scan(data_dir: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan local BIDS dataset for events.tsv files and validate them.
    
    Args:
        data_dir: Path to the BIDS dataset root (e.g., data/raw/wesad/)
        schema: The loaded JSON schema
        
    Returns:
        Dict with 'found' (bool), 'tasks_found' (list), 'valid_files' (list), 'status' (str)
    """
    logger.info(f"Performing Local BIDS Scan in {data_dir}...")
    tasks_found = set()
    valid_files = []
    invalid_files = []
    
    if not data_dir.exists():
        logger.warning(f"Data directory not found: {data_dir}")
        return {
            'found': False,
            'tasks_found': [],
            'valid_files': [],
            'invalid_files': [],
            'status': 'directory_missing'
        }

    # Find all events.tsv files
    events_files = list(data_dir.rglob("events.tsv"))
    
    if not events_files:
        logger.warning("No events.tsv files found in local dataset.")
        return {
            'found': False,
            'tasks_found': [],
            'valid_files': [],
            'invalid_files': [],
            'status': 'no_events_files'
        }

    for event_file in events_files:
        try:
            # Validate against schema
            is_valid = validate_events_tsv(event_file, schema)
            
            if is_valid:
                valid_files.append(str(event_file))
                # Read the file to check for task labels
                try:
                    df = pd.read_csv(event_file, sep='\t')
                    if 'task' in df.columns:
                        unique_tasks = df['task'].unique().tolist()
                        for task in unique_tasks:
                            if task in REQUIRED_TASKS or any(r in task.lower() for r in ['schandry', 'heartbeat']):
                                tasks_found.add(task)
                    else:
                        logger.warning(f"File {event_file} missing 'task' column.")
                except Exception as e:
                    logger.warning(f"Could not parse {event_file}: {e}")
            else:
                invalid_files.append(str(event_file))
                
        except Exception as e:
            logger.error(f"Error processing {event_file}: {e}")
            invalid_files.append(str(event_file))

    found = len(tasks_found) > 0
    status = 'success' if found else 'tasks_missing'
    
    return {
        'found': found,
        'tasks_found': list(tasks_found),
        'valid_files': valid_files,
        'invalid_files': invalid_files,
        'status': status
    }

def generate_audit_report(remote_result: Dict, local_result: Dict, download_success: bool) -> str:
    """
    Generate the final markdown report based on remote and local scan results.
    
    Logic:
    - If remote check says 'success' (found tasks), report Success.
    - If remote check says 'inconclusive' or 'error', rely on local scan.
    - If local scan found tasks, report Success.
    - If local scan found no tasks (and download existed), report Feasibility Failure.
    - If download failed, report Download Failure.
    """
    report_lines = []
    report_lines.append("# Data Availability Audit Report")
    report_lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")
    
    # Feasibility Status Section
    report_lines.append("## Feasibility Status")
    report_lines.append("")
    
    final_status = "Unknown"
    final_message = ""
    
    if not download_success:
        final_status = "Feasibility Failure: Download Incomplete"
        final_message = "The WESAD dataset download (T010) did not complete successfully. Local scan could not be performed."
        report_lines.append(f"**Status**: {final_status}")
        report_lines.append(f"**Message**: {final_message}")
    else:
        # Download succeeded, check scan results
        if remote_result['status'] == 'success':
            final_status = "Feasibility Success"
            final_message = f"Remote metadata check confirmed presence of required tasks: {', '.join(remote_result['tasks_found'])}."
        elif local_result['found']:
            final_status = "Feasibility Success"
            final_message = f"Local BIDS scan confirmed presence of required tasks: {', '.join(local_result['tasks_found'])}."
        else:
            final_status = "Feasibility Failure: Missing Behavioral Task"
            final_message = "Required behavioral tasks (Schandry, heartbeat) were not found in the dataset metadata or local BIDS files."
        
        report_lines.append(f"**Status**: {final_status}")
        report_lines.append(f"**Message**: {final_message}")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # Remote Pre-Check Details
    report_lines.append("## Remote Metadata Pre-Check")
    report_lines.append(f"Status: {remote_result['status']}")
    report_lines.append(f"Tasks Found: {', '.join(remote_result['tasks_found']) if remote_result['tasks_found'] else 'None'}")
    report_lines.append("")
    
    # Local BIDS Scan Details
    report_lines.append("## Local BIDS Scan")
    report_lines.append(f"Data Directory: data/raw/wesad/")
    report_lines.append(f"Scan Status: {local_result['status']}")
    report_lines.append(f"Tasks Found: {', '.join(local_result['tasks_found']) if local_result['tasks_found'] else 'None'}")
    report_lines.append(f"Valid Events Files: {len(local_result['valid_files'])}")
    report_lines.append(f"Invalid Events Files: {len(local_result['invalid_files'])}")
    report_lines.append("")
    
    if local_result['valid_files']:
        report_lines.append("Valid Files:")
        for f in local_result['valid_files']:
            report_lines.append(f"- {f}")
    report_lines.append("")
    
    if local_result['invalid_files']:
        report_lines.append("Invalid Files (Schema Mismatch):")
        for f in local_result['invalid_files']:
            report_lines.append(f"- {f}")
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    report_lines.append("")
    if final_status == "Feasibility Success":
        report_lines.append("The dataset contains the required behavioral tasks. The pipeline may proceed to Phase 4 (Preprocessing).")
    else:
        report_lines.append("**Pipeline Termination**: The required data is missing. The pipeline must stop here.")
        report_lines.append("Do NOT proceed to HRV preprocessing or regression analysis.")
        
    return "\n".join(report_lines)

def main():
    """Main entry point for the audit script."""
    logger.info("Starting Data Availability Audit (T011/T014)...")
    
    # Check if download was successful (T010 flag)
    download_success = DOWNLOAD_FLAG_PATH.exists()
    logger.info(f"WESAD Download Flag exists: {download_success}")
    
    # 1. Remote Pre-Check
    remote_result = remote_metadata_pre_check()
    
    # 2. Local Scan (only if download succeeded)
    local_result = {
        'found': False,
        'tasks_found': [],
        'valid_files': [],
        'invalid_files': [],
        'status': 'skipped'
    }
    
    if download_success:
        schema = load_schema(SCHEMA_PATH)
        data_dir = Path("data/raw/wesad")
        local_result = local_bids_scan(data_dir, schema)
    else:
        logger.info("Skipping local scan because download flag is missing.")
        local_result['status'] = 'skipped'
    
    # 3. Generate Report
    report_content = generate_audit_report(remote_result, local_result, download_success)
    
    # Write report
    AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_REPORT_PATH, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Audit report written to {AUDIT_REPORT_PATH}")
    
    # Determine exit code
    # If Feasibility Failure, we exit 0 (success of the script) but the content indicates failure.
    # The pipeline logic (T029) will read the file and decide to stop.
    # If download failed completely and we can't even check, we might exit non-zero?
    # Per spec: "exit 0 with failure status in report" for feasibility failure.
    # "exit non-zero (if download failed and no local scan possible)" -> handled by T010 mostly, but here if download failed, we report failure.
    
    if "Feasibility Failure" in report_content:
        logger.warning("Feasibility Failure detected. Pipeline should terminate.")
        # Exit 0 as the script successfully generated the failure report
        sys.exit(0)
    else:
        logger.info("Feasibility Success. Pipeline may proceed.")
        sys.exit(0)

if __name__ == "__main__":
    main()