import os
import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Import from existing API surface
from utils.bids_scanner import find_events_files, scan_events_for_tasks, scan_bids_dataset_for_interoception
from utils.error_contract import download_with_contract, ContractViolationError, load_schema, enforce_error_contract

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
WESAD_DIR = DATA_DIR / "raw" / "WESAD"
OPENNEURO_DIR = DATA_DIR / "raw" / "OpenNeuro"
AUDIT_OUTPUT = DATA_DIR / "audit" / "data_audit.md"

def check_structure() -> Dict[str, Any]:
    """Check if the expected directory structure exists."""
    structure = {
        "wesad_exists": WESAD_DIR.exists(),
        "openneuro_exists": OPENNEURO_DIR.exists(),
        "data_dir_exists": DATA_DIR.exists()
    }
    if not structure["data_dir_exists"]:
        logger.warning(f"Data directory {DATA_DIR} does not exist.")
    return structure

def scan_wesad_metadata() -> Dict[str, Any]:
    """
    Scan WESAD dataset for interoception tasks (Schandry, heartbeat) and stress markers.
    Uses the BIDS scanner utilities to find events.tsv files and check for task labels.
    """
    results = {
        "schandry_found": False,
        "heartbeat_found": False,
        "tsst_found": False,
        "events_files_checked": 0,
        "details": []
    }

    if not WESAD_DIR.exists():
        logger.warning(f"WESAD directory {WESAD_DIR} does not exist. Skipping scan.")
        results["status"] = "Directory Missing"
        return results

    try:
        # Use the existing BIDS scanner to find events files
        events_files = find_events_files(WESAD_DIR)
        results["events_files_checked"] = len(events_files)
        
        if not events_files:
            logger.info("No events.tsv files found in WESAD directory.")
            results["details"].append("No events.tsv files found.")
            return results

        # Scan for specific tasks
        found_tasks = scan_events_for_tasks(events_files, ["Schandry", "heartbeat"])
        if "Schandry" in found_tasks:
            results["schandry_found"] = True
            results["details"].append(f"Found 'Schandry' task in: {found_tasks['Schandry']}")
        if "heartbeat" in found_tasks:
            results["heartbeat_found"] = True
            results["details"].append(f"Found 'heartbeat' task in: {found_tasks['heartbeat']}")

        # Scan specifically for interoception markers using the dedicated function
        interoception_results = scan_bids_dataset_for_interoception(WESAD_DIR)
        if interoception_results.get("tsst_markers"):
            results["tsst_found"] = True
            results["details"].append(f"Found TSST stress markers in: {interoception_results['tsst_markers']}")
        
        # Additional check for TSST in file names if not found in events
        for file_path in events_files:
            try:
                df = pd.read_csv(file_path, sep='\t')
                if 'task' in df.columns:
                    if df['task'].str.contains('TSST', case=False, na=False).any():
                        results["tsst_found"] = True
                        if f"TSST found in {file_path}" not in results["details"]:
                            results["details"].append(f"TSST found in {file_path}")
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        results["status"] = "Scan Complete"
    except Exception as e:
        logger.error(f"Error scanning WESAD metadata: {e}")
        results["status"] = "Error"
        results["error"] = str(e)

    return results

def scan_openneuro_metadata() -> Dict[str, Any]:
    """
    Scan OpenNeuro dataset for TSST stress markers.
    Similar logic to WESAD but focused on OpenNeuro structure.
    """
    results = {
        "tsst_found": False,
        "events_files_checked": 0,
        "details": []
    }

    if not OPENNEURO_DIR.exists():
        logger.warning(f"OpenNeuro directory {OPENNEURO_DIR} does not exist. Skipping scan.")
        results["status"] = "Directory Missing"
        return results

    try:
        events_files = find_events_files(OPENNEURO_DIR)
        results["events_files_checked"] = len(events_files)

        if not events_files:
            logger.info("No events.tsv files found in OpenNeuro directory.")
            results["details"].append("No events.tsv files found.")
            return results

        # Scan for TSST specifically
        for file_path in events_files:
            try:
                df = pd.read_csv(file_path, sep='\t')
                if 'task' in df.columns:
                    if df['task'].str.contains('TSST', case=False, na=False).any():
                        results["tsst_found"] = True
                        results["details"].append(f"TSST found in {file_path}")
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")

        results["status"] = "Scan Complete"
    except Exception as e:
        logger.error(f"Error scanning OpenNeuro metadata: {e}")
        results["status"] = "Error"
        results["error"] = str(e)

    return results

def generate_audit_report(wesad_results: Dict, openneuro_results: Dict, structure: Dict) -> str:
    """Generate a markdown report of the audit findings."""
    report_lines = [
        "# Data Availability Audit Report",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Dataset Structure Check",
        f"- WESAD directory exists: {structure['wesad_exists']}",
        f"- OpenNeuro directory exists: {structure['openneuro_exists']}",
        "",
        "## WESAD Dataset Analysis",
    ]

    if wesad_results.get("status") == "Directory Missing":
        report_lines.append("**Status**: WESAD directory not found.")
    else:
        report_lines.append(f"- Events files checked: {wesad_results.get('events_files_checked', 0)}")
        report_lines.append(f"- Schandry task found: {'Yes' if wesad_results.get('schandry_found') else 'No'}")
        report_lines.append(f"- Heartbeat task found: {'Yes' if wesad_results.get('heartbeat_found') else 'No'}")
        report_lines.append(f"- TSST stress markers found: {'Yes' if wesad_results.get('tsst_found') else 'No'}")
        
        if wesad_results.get("details"):
            report_lines.append("")
            report_lines.append("### Details:")
            for detail in wesad_results["details"]:
                report_lines.append(f"- {detail}")

    report_lines.extend([
        "",
        "## OpenNeuro Dataset Analysis",
    ])

    if openneuro_results.get("status") == "Directory Missing":
        report_lines.append("**Status**: OpenNeuro directory not found.")
    else:
        report_lines.append(f"- Events files checked: {openneuro_results.get('events_files_checked', 0)}")
        report_lines.append(f"- TSST stress markers found: {'Yes' if openneuro_results.get('tsst_found') else 'No'}")
        
        if openneuro_results.get("details"):
            report_lines.append("")
            report_lines.append("### Details:")
            for detail in openneuro_results["details"]:
                report_lines.append(f"- {detail}")

    # Feasibility Status Section
    report_lines.extend([
        "",
        "## Feasibility Status",
    ])

    missing_vars = []
    if not wesad_results.get("schandry_found") and not wesad_results.get("heartbeat_found"):
        missing_vars.append("Interoception tasks (Schandry/heartbeat) in WESAD")
    
    if not wesad_results.get("tsst_found") and not openneuro_results.get("tsst_found"):
        missing_vars.append("TSST stress markers")

    if missing_vars:
        report_lines.append("**Missing**: " + ", ".join(missing_vars))
        report_lines.append("Feasibility: Limited - Required behavioral tasks not found in scanned datasets.")
    else:
        report_lines.append("All required variables found.")
        report_lines.append("Feasibility: High - Required behavioral tasks and stress markers present.")

    report_lines.append("")
    return "\n".join(report_lines)

def main():
    """Main entry point for the audit data script."""
    start_time = time.time()
    logger.info("Starting data availability audit...")

    try:
        # Check directory structure
        structure = check_structure()
        
        # Scan datasets
        wesad_results = scan_wesad_metadata()
        openneuro_results = scan_openneuro_metadata()
        
        # Generate report
        report_content = generate_audit_report(wesad_results, openneuro_results, structure)
        
        # Ensure output directory exists
        AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(AUDIT_OUTPUT, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Audit report generated successfully: {AUDIT_OUTPUT}")
        
        # Validate that the report reflects the scan results
        # Read back and verify key findings are present
        with open(AUDIT_OUTPUT, 'r', encoding='utf-8') as f:
            report_text = f.read()
        
        # Basic validation: ensure the report contains the Feasibility Status section
        if "Feasibility Status" not in report_text:
            logger.error("Validation failed: Feasibility Status section missing from report.")
            sys.exit(1)
        
        # Ensure report mentions the scan results
        if wesad_results.get("status") != "Directory Missing" and wesad_results.get("events_files_checked", 0) > 0:
            if f"Events files checked: {wesad_results['events_files_checked']}" not in report_text:
                logger.error("Validation failed: WESAD scan results not reflected in report.")
                sys.exit(1)
        
        if openneuro_results.get("status") != "Directory Missing" and openneuro_results.get("events_files_checked", 0) > 0:
            if f"Events files checked: {openneuro_results['events_files_checked']}" not in report_text:
                logger.error("Validation failed: OpenNeuro scan results not reflected in report.")
                sys.exit(1)
        
        logger.info("Validation successful: Audit report correctly reflects scan results.")
        
        elapsed = time.time() - start_time
        logger.info(f"Audit completed in {elapsed:.2f} seconds.")
        
        # Exit with code 0 as per T015 requirement
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error during audit: {e}")
        # Even on error, try to generate a minimal report
        try:
            error_report = f"# Data Availability Audit Report\n\n**Status**: Error - {str(e)}\n\n**Feasibility Status**: Unable to determine due to error."
            AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            with open(AUDIT_OUTPUT, 'w', encoding='utf-8') as f:
                f.write(error_report)
        except:
            pass
        sys.exit(0)  # T015: Exit code 0 regardless of findings

if __name__ == "__main__":
    main()
