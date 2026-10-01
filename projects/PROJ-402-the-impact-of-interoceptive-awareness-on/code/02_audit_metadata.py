import os
import sys
import json
import logging
import time
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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
OPENNEURO_INDEX_PATH = Path("data/raw/openneuro/index.json")
WESAD_SCAN_RESULTS_PATH = Path("data/audit/wesad_scan_results.json")
OPENNEURO_SCAN_RESULTS_PATH = Path("data/audit/openneuro_scan_results.json")
AGGREGATED_RESULTS_PATH = Path("data/audit/scan_results.json")
AUDIT_REPORT_PATH = Path("results/data_audit.md")

# Target tasks for interoception behavioral task detection
BEHAVIORAL_TASKS = {'schandry', 'heartbeat'}
PHASE_TASKS = {'tsst', 'rest', 'baseline'}
ALL_TARGET_TASKS = BEHAVIORAL_TASKS | PHASE_TASKS

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load JSON schema from file."""
    import yaml
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading schema: {e}")
        raise

def validate_events_tsv(events_file: Path, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate an events.tsv file against the schema."""
    import pandas as pd
    import jsonschema
    
    errors = []
    try:
        df = pd.read_csv(events_file, sep='\t')
        
        # Check required columns
        if 'task' not in df.columns:
            errors.append("Missing required 'task' column")
            return False, errors
        
        # Validate task values
        valid_tasks = list(schema['properties']['task']['enum'])
        invalid_tasks = [t for t in df['task'].unique() if t not in valid_tasks]
        if invalid_tasks:
            errors.append(f"Invalid task values found: {invalid_tasks}")
        
        # Check for numerical columns
        for col in ['onset', 'duration']:
            if col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    errors.append(f"Column '{col}' must be numeric")
        
        return len(errors) == 0, errors
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return False, errors

def remote_metadata_pre_check() -> Dict[str, Any]:
    """Pre-check remote metadata availability (placeholder for future implementation)."""
    logger.info("Performing remote metadata pre-check...")
    # This would typically check if OpenNeuro index exists
    return {"status": "checked", "remote_available": True}

def local_bids_scan(wesad_dir: Path) -> Dict[str, Any]:
    """Scan local BIDS directory for events.tsv files and extract task information."""
    import pandas as pd
    
    results = {
        "source": "wesad_local",
        "status": "success",
        "subjects": [],
        "tasks_found": set(),
        "files_scanned": []
    }
    
    if not wesad_dir.exists():
        logger.warning(f"WESAD directory not found: {wesad_dir}")
        results["status"] = "directory_not_found"
        return results
    
    # Find all events.tsv files
    events_files = list(wesad_dir.rglob("**/events.tsv"))
    
    if not events_files:
        logger.warning("No events.tsv files found in WESAD directory")
        results["status"] = "no_events_files"
        return results
    
    for events_file in events_files:
        try:
            df = pd.read_csv(events_file, sep='\t')
            
            if 'task' not in df.columns:
                logger.warning(f"No 'task' column in {events_file}")
                continue
            
            tasks_in_file = df['task'].unique().tolist()
            results["tasks_found"].update(tasks_in_file)
            results["files_scanned"].append(str(events_file))
            
            # Extract subject ID from path
            subject_id = events_file.parent.name.replace('sub-', '')
            
            subject_data = {
                "subject_id": subject_id,
                "file": str(events_file),
                "tasks": tasks_in_file
            }
            results["subjects"].append(subject_data)
            
            logger.info(f"Scanned {events_file}: found tasks {tasks_in_file}")
            
        except Exception as e:
            logger.error(f"Error processing {events_file}: {e}")
            continue
    
    results["tasks_found"] = list(results["tasks_found"])
    return results

def scan_openneuro_index() -> Dict[str, Any]:
    """
    Scan the downloaded OpenNeuro index for studies containing 'TSST' AND ('heartbeat' OR 'interoception').
    This implements T011b: Index Scan for OpenNeuro.
    """
    logger.info("Starting OpenNeuro index scan...")
    
    results = {
        "source": "openneuro_index",
        "status": "success",
        "matching_studies": [],
        "total_studies_scanned": 0,
        "criteria": {
            "required_tasks": ["TSST"],
            "alternative_tasks": ["heartbeat", "interoception"],
            "logic": "TSST AND (heartbeat OR interoception)"
        }
    }
    
    if not OPENNEURO_INDEX_PATH.exists():
        logger.error(f"OpenNeuro index file not found: {OPENNEURO_INDEX_PATH}")
        results["status"] = "index_not_found"
        return results
    
    try:
        with open(OPENNEURO_INDEX_PATH, 'r') as f:
            index_data = json.load(f)
        
        logger.info(f"Loaded OpenNeuro index with {len(index_data)} entries")
        results["total_studies_scanned"] = len(index_data)
        
        for study in index_data:
            study_id = study.get('id', study.get('dataset', 'unknown'))
            tasks = study.get('tasks', [])
            
            # Normalize tasks to lowercase for comparison
            tasks_lower = [t.lower() for t in tasks]
            
            # Check for TSST (required)
            has_tsst = 'tsst' in tasks_lower
            
            # Check for heartbeat OR interoception
            has_interoception = 'heartbeat' in tasks_lower or 'interoception' in tasks_lower
            
            if has_tsst and has_interoception:
                matching_entry = {
                    "study_id": study_id,
                    "original_tasks": tasks,
                    "matched_criteria": True,
                    "has_tsst": True,
                    "has_interoception": has_interoception,
                    "source_url": study.get('url', study.get('download_url', 'unknown'))
                }
                results["matching_studies"].append(matching_entry)
                logger.info(f"Found matching study: {study_id} with tasks {tasks}")
        
        logger.info(f"Scan complete. Found {len(results['matching_studies'])} matching studies.")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in OpenNeuro index: {e}")
        results["status"] = "invalid_json"
    except Exception as e:
        logger.error(f"Error scanning OpenNeuro index: {e}")
        results["status"] = "scan_error"
    
    return results

def aggregate_scan_results(wesad_results: Dict[str, Any], openneuro_results: Dict[str, Any]) -> Dict[str, Any]:
    """Merge WESAD and OpenNeuro scan results and determine feasibility."""
    
    aggregated = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sources": {
            "wesad": wesad_results,
            "openneuro": openneuro_results
        },
        "feasibility_status": "unknown",
        "summary": {
            "total_sources_checked": 2,
            "wesad_available": wesad_results.get("status") != "directory_not_found",
            "openneuro_available": openneuro_results.get("status") == "success",
            "behavioral_tasks_found": [],
            "total_matching_studies": 0
        }
    }
    
    # Collect all tasks found
    all_tasks = set()
    if wesad_results.get("status") == "success":
        all_tasks.update(wesad_results.get("tasks_found", []))
    
    # Check OpenNeuro for behavioral tasks
    if openneuro_results.get("status") == "success":
        aggregated["summary"]["total_matching_studies"] = len(openneuro_results.get("matching_studies", []))
        # The matching studies by definition have heartbeat/interoception
        if aggregated["summary"]["total_matching_studies"] > 0:
            all_tasks.update(["heartbeat"])  # Indicates behavioral task presence
    
    # Determine feasibility
    behavioral_tasks_in_data = [t for t in all_tasks if t.lower() in BEHAVIORAL_TASKS]
    
    if not behavioral_tasks_in_data:
        if not aggregated["summary"]["wesad_available"] and not aggregated["summary"]["openneuro_available"]:
            aggregated["feasibility_status"] = "Feasibility Failure: Dataset Unavailable"
            aggregated["summary"]["reason"] = "No data sources available"
        elif aggregated["summary"]["wesad_available"] or aggregated["summary"]["openneuro_available"]:
            aggregated["feasibility_status"] = "Feasibility Failure: Missing Behavioral Task"
            aggregated["summary"]["reason"] = "No Schandry or heartbeat tasks found in available data"
        else:
            aggregated["feasibility_status"] = "Feasibility Failure: Unknown"
    else:
        aggregated["feasibility_status"] = "Feasibility Success"
        aggregated["summary"]["reason"] = f"Found behavioral tasks: {behavioral_tasks_in_data}"
    
    aggregated["summary"]["behavioral_tasks_found"] = behavioral_tasks_in_data
    
    return aggregated

def generate_audit_report(aggregated_results: Dict[str, Any]) -> None:
    """Generate the final markdown audit report."""
    
    report_lines = [
        "# Data Availability Audit Report",
        f"Generated: {aggregated_results['timestamp']}",
        "",
        "## Executive Summary",
        f"**Feasibility Status**: {aggregated_results['feasibility_status']}",
        "",
        "## Data Sources Checked",
        f"- WESAD: {'Available' if aggregated_results['summary']['wesad_available'] else 'Unavailable'}",
        f"- OpenNeuro: {'Available' if aggregated_results['summary']['openneuro_available'] else 'Unavailable'}",
        "",
        "## Behavioral Task Detection",
        f"Tasks Found: {aggregated_results['summary']['behavioral_tasks_found']}",
        f"Reason: {aggregated_results['summary'].get('reason', 'N/A')}",
        "",
        "## Detailed Results",
        "### WESAD Scan",
        f"- Status: {aggregated_results['sources']['wesad'].get('status', 'N/A')}",
        f"- Subjects Scanned: {len(aggregated_results['sources']['wesad'].get('subjects', []))}",
        f"- Tasks Found: {aggregated_results['sources']['wesad'].get('tasks_found', [])}",
        "",
        "### OpenNeuro Index Scan",
        f"- Status: {aggregated_results['sources']['openneuro'].get('status', 'N/A')}",
        f"- Total Studies Scanned: {aggregated_results['sources']['openneuro'].get('total_studies_scanned', 0)}",
        f"- Matching Studies (TSST + Interoception): {aggregated_results['sources']['openneuro'].get('matching_studies', [])}",
        "",
        "## Conclusion",
    ]
    
    if aggregated_results['feasibility_status'] == "Feasibility Success":
        report_lines.append("The dataset contains the required behavioral tasks (Schandry or heartbeat) for interoception analysis.")
        report_lines.append("Pipeline can proceed to Phase 4 (Preprocessing).")
    elif "Dataset Unavailable" in aggregated_results['feasibility_status']:
        report_lines.append("No data sources were available for analysis.")
        report_lines.append("Pipeline cannot proceed without data.")
    else:
        report_lines.append("Data sources exist but lack the required behavioral tasks.")
        report_lines.append("Pipeline will calculate Upper Bound of Detectable Effect (UBDE) instead of regression.")
    
    report_content = "\n".join(report_lines)
    
    # Ensure results directory exists
    AUDIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(AUDIT_REPORT_PATH, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Audit report generated: {AUDIT_REPORT_PATH}")

def main():
    """Main entry point for the audit metadata script."""
    logger.info("Starting audit metadata script...")
    start_time = time.time()
    
    try:
        # Step 1: Pre-check remote metadata
        remote_check = remote_metadata_pre_check()
        
        # Step 2: Perform Local BIDS Scan (WESAD) - T011a
        wesad_dir = Path("data/raw/wesad")
        wesad_results = local_bids_scan(wesad_dir)
        
        # Save WESAD scan results
        WESAD_SCAN_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(WESAD_SCAN_RESULTS_PATH, 'w') as f:
            json.dump(wesad_results, f, indent=2)
        logger.info(f"WESAD scan results saved to {WESAD_SCAN_RESULTS_PATH}")
        
        # Step 3: Perform Index Scan (OpenNeuro) - T011b
        openneuro_results = scan_openneuro_index()
        
        # Save OpenNeuro scan results
        OPENNEURO_SCAN_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OPENNEURO_SCAN_RESULTS_PATH, 'w') as f:
            json.dump(openneuro_results, f, indent=2)
        logger.info(f"OpenNeuro scan results saved to {OPENNEURO_SCAN_RESULTS_PATH}")
        
        # Step 4: Aggregate Results - T011c
        aggregated_results = aggregate_scan_results(wesad_results, openneuro_results)
        
        # Save aggregated results
        AGGREGATED_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AGGREGATED_RESULTS_PATH, 'w') as f:
            json.dump(aggregated_results, f, indent=2)
        logger.info(f"Aggregated results saved to {AGGREGATED_RESULTS_PATH}")
        
        # Step 5: Generate Final Report - T014
        generate_audit_report(aggregated_results)
        
        duration = time.time() - start_time
        logger.info(f"Audit completed in {duration:.2f} seconds")
        logger.info(f"Feasibility Status: {aggregated_results['feasibility_status']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Audit script failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())