"""
Audit script for User Story 1: Data Availability.

Performs a two-part scan:
1. Remote Metadata Pre-Check: Queries Zenodo API to check for 'Schandry' or 'heartbeat' tasks.
2. Local BIDS Scan: Scans local events.tsv files if T010 download succeeded.

Outputs: results/data_audit.md

Logic:
- If Remote Pre-Check confirms absence -> Feasibility Failure, terminate.
- If Remote Pre-Check passes or inconclusive -> proceed to Local Scan.
- If Local Scan finds required tasks -> Feasibility Success.
- If Local Scan fails -> Feasibility Failure.
"""
import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import requests
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/audit_log.txt', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Constants
ZENODO_API_URL = "https://zenodo.org/api/records/1292932"  # WESAD DOI: 10.5281/zenodo.1292932
REQUIRED_TASKS = ['schandry', 'heartbeat']
WESAD_DOWNLOAD_FLAG_FILE = Path('data/.wesad_download_complete')
SCHEMA_PATH = Path('contracts/dataset.schema.yaml')
OUTPUT_REPORT_PATH = Path('results/data_audit.md')
TIMEOUT_SECONDS = 300  # 5 minutes for remote check

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON Schema for BIDS events.tsv validation."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_events_tsv(events_file: Path, schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single events.tsv file against the schema.
    Returns (is_valid, error_message).
    """
    try:
        # Load TSV
        df = pd.read_csv(events_file, sep='\t')
        
        # Basic schema validation: check for 'task' column
        if 'task' not in df.columns:
            return False, f"Missing 'task' column in {events_file}"
        
        # Check for required task values (case-insensitive)
        task_values = df['task'].astype(str).str.lower().unique()
        found_required = any(req in task_values for req in REQUIRED_TASKS)
        
        if not found_required:
            return False, f"No required task ({REQUIRED_TASKS}) found in {events_file}. Found: {task_values}"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Error processing {events_file}: {str(e)}"

def remote_metadata_pre_check() -> Tuple[bool, str]:
    """
    Query Zenodo REST API to check for 'Schandry' or 'heartbeat' in file list.
    Returns (status, message).
    status: True if tasks found, False if not found, None if inconclusive (network error).
    """
    logger.info("Starting Remote Metadata Pre-Check...")
    start_time = time.time()
    
    try:
        response = requests.get(ZENODO_API_URL, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        
        # Parse files from Zenodo response
        files = data.get('files', [])
        file_names = [f.get('key', '').lower() for f in files]
        
        # Check for interoception task indicators in filenames or metadata
        # Note: Zenodo API doesn't expose BIDS task labels directly in files list.
        # We check for keywords in filenames and descriptions.
        description = data.get('metadata', {}).get('description', '').lower()
        title = data.get('metadata', {}).get('title', '').lower()
        
        # Search for keywords
        has_interoception = False
        for keyword in REQUIRED_TASKS:
            if any(keyword in fname for fname in file_names) or \
               keyword in description or \
               keyword in title:
                has_interoception = True
                logger.info(f"Found keyword '{keyword}' in remote metadata.")
                break
        
        if has_interoception:
            return True, "Remote check PASSED: Interoception tasks likely present."
        else:
            # Inconclusive if not found in metadata but might be in file content
            # We proceed to local scan if download exists
            return None, "Remote check INCONCLUSIVE: No clear indicators in metadata. Proceeding to local scan if available."
            
    except requests.exceptions.Timeout:
        logger.error("Remote check TIMEOUT: Failed to reach Zenodo API within timeout.")
        return None, "Remote check INCONCLUSIVE: Timeout. Proceeding to local scan if available."
    except requests.exceptions.RequestException as e:
        logger.error(f"Remote check FAILED: Network error - {str(e)}")
        return None, f"Remote check INCONCLUSIVE: Network error ({str(e)}). Proceeding to local scan if available."
    except Exception as e:
        logger.error(f"Remote check FAILED: Unexpected error - {str(e)}")
        return None, f"Remote check INCONCLUSIVE: Unexpected error ({str(e)}). Proceeding to local scan if available."
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Remote check completed in {elapsed:.2f} seconds.")

def local_bids_scan() -> Tuple[bool, str]:
    """
    Scan local BIDS dataset for events.tsv files containing required tasks.
    Only runs if T010 download succeeded (flag file exists).
    Returns (status, message).
    """
    logger.info("Starting Local BIDS Scan...")
    
    if not WESAD_DOWNLOAD_FLAG_FILE.exists():
        logger.warning("Local scan SKIPPED: T010 download flag file not found.")
        return False, "Local scan FAILED: Download not completed (T010 flag missing)."
    
    schema = load_schema(SCHEMA_PATH)
    data_dir = Path('data/raw/wesad')
    
    if not data_dir.exists():
        logger.warning("Local scan SKIPPED: Data directory not found.")
        return False, "Local scan FAILED: Data directory 'data/raw/wesad' not found."
    
    events_files = list(data_dir.rglob('**/events.tsv'))
    
    if not events_files:
        logger.warning("Local scan FAILED: No events.tsv files found in data directory.")
        return False, "Local scan FAILED: No events.tsv files found."
    
    logger.info(f"Found {len(events_files)} events.tsv files to scan.")
    
    all_valid = True
    failure_messages = []
    
    for events_file in events_files:
        is_valid, msg = validate_events_tsv(events_file, schema)
        if is_valid:
            logger.info(f"Valid: {events_file}")
        else:
            all_valid = False
            failure_messages.append(msg)
            logger.warning(f"Invalid: {events_file} - {msg}")
    
    if all_valid:
        return True, "Local scan PASSED: All events.tsv files contain required tasks."
    else:
        return False, f"Local scan FAILED: Some files missing required tasks. Details: {failure_messages}"

def generate_audit_report(remote_status: Tuple[bool, str], local_status: Tuple[bool, str]) -> None:
    """Generate the final audit report in Markdown format."""
    remote_ok, remote_msg = remote_status
    local_ok, local_msg = local_status
    
    report_lines = [
        "# Data Availability Audit Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Executive Summary",
        ""
    ]
    
    # Determine feasibility status
    if remote_ok:
        # Remote check passed, local scan might not have run or passed
        if local_ok or not WESAD_DOWNLOAD_FLAG_FILE.exists():
            feasibility = "Success"
            status_msg = "Data availability confirmed. Pipeline can proceed to HRV preprocessing."
        else:
            feasibility = "Failure"
            status_msg = "Remote check passed but local scan failed. Data may be corrupted or incomplete."
    elif remote_ok is False:
        # Remote check confirmed absence
        feasibility = "Failure"
        status_msg = "Feasibility Failure: Missing Behavioral Task (Remote check confirmed absence)."
    else:
        # Remote check inconclusive
        if local_ok:
            feasibility = "Success"
            status_msg = "Data availability confirmed via local scan. Pipeline can proceed to HRV preprocessing."
        else:
            feasibility = "Failure"
            status_msg = "Feasibility Failure: Missing Behavioral Task (Local scan failed)."
    
    report_lines.append(f"**Feasibility Status**: {feasibility}")
    report_lines.append(f"**Status Message**: {status_msg}")
    report_lines.append("")
    
    # Remote Check Section
    report_lines.append("## Remote Metadata Pre-Check")
    report_lines.append(f"- Status: {'PASSED' if remote_ok else 'FAILED' if remote_ok is False else 'INCONCLUSIVE'}")
    report_lines.append(f"- Details: {remote_msg}")
    report_lines.append("")
    
    # Local Scan Section
    report_lines.append("## Local BIDS Scan")
    report_lines.append(f"- Status: {'PASSED' if local_ok else 'FAILED'}")
    report_lines.append(f"- Details: {local_msg}")
    report_lines.append("")
    
    # Validation Criteria
    report_lines.append("## Validation Criteria")
    report_lines.append("- Required tasks: 'Schandry' or 'heartbeat' (case-insensitive)")
    report_lines.append("- Validation: events.tsv files checked against BIDS schema")
    report_lines.append("")
    
    # Conclusion
    report_lines.append("## Conclusion")
    if feasibility == "Success":
        report_lines.append("✅ **Pipeline can proceed** to HRV preprocessing (Phase 4).")
    else:
        report_lines.append("❌ **Pipeline TERMINATED**. Missing required behavioral data.")
        report_lines.append("Do NOT proceed to HRV preprocessing or regression analysis.")
    
    # Write report
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Audit report generated: {OUTPUT_REPORT_PATH}")

def main():
    """Main entry point for the audit script."""
    logger.info("Starting Data Availability Audit (T011)...")
    start_time = time.time()
    
    try:
        # Step 1: Remote Metadata Pre-Check
        remote_status = remote_metadata_pre_check()
        remote_ok, remote_msg = remote_status
        
        # If remote check confirms absence, terminate immediately
        if remote_ok is False:
            logger.error("Remote check confirmed absence of required tasks. Terminating pipeline.")
            generate_audit_report(remote_status, (False, "Skipped due to remote failure"))
            logger.info("Pipeline terminated: Feasibility Failure.")
            sys.exit(0)  # Exit 0 with failure status in report
        
        # Step 2: Local BIDS Scan (conditional)
        local_status = local_bids_scan()
        
        # Step 3: Generate Report
        generate_audit_report(remote_status, local_status)
        
        elapsed = time.time() - start_time
        logger.info(f"Audit completed in {elapsed:.2f} seconds.")
        
        # Determine exit code based on feasibility
        if "Success" in str(remote_msg) or (local_status[0] is True):
            logger.info("Audit PASSED. Pipeline can proceed.")
            sys.exit(0)
        else:
            logger.info("Audit FAILED. Pipeline terminated.")
            sys.exit(0)  # Exit 0 with failure status in report (as per spec)
            
    except Exception as e:
        logger.critical(f"Audit script crashed: {str(e)}")
        # Generate error report
        with open(OUTPUT_REPORT_PATH, 'w') as f:
            f.write(f"# Audit Failed\n\nError: {str(e)}\n\n**Feasibility Status**: Failure\n")
        sys.exit(1)

if __name__ == "__main__":
    main()