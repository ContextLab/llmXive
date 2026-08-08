import os
import sys
import json
from pathlib import Path
from datetime import datetime

def check_plan_for_amendment(verification_report_path: Path) -> dict:
    """
    Read the download status verification report and determine if an amendment is needed.
    
    Logic:
    1. If recipe1m is "FAILED", raise error (Pipeline Halt).
    2. If flavordb or counterfactual is "FAILED" or "INVALID_SCHEMA", 
       set methodology to "Correlational Analysis" and proxy_source to "Recipe1M".
    3. If all "SUCCESS", set methodology to "Causal Independence" and proxy_source to null.
    
    Returns a dict with status, methodology, and proxy_source.
    """
    if not verification_report_path.exists():
        raise FileNotFoundError(f"Verification report not found: {verification_report_path}")
    
    with open(verification_report_path, 'r') as f:
        status_data = json.load(f)
    
    # Check Recipe1M status - critical dependency
    recipe1m_status = status_data.get('recipe1m', {}).get('status')
    if recipe1m_status == "FAILED":
        raise RuntimeError("Pipeline Halt: Recipe1M download failed. This is a critical dependency.")
    
    # Check other datasets
    flavordb_status = status_data.get('flavordb', {}).get('status')
    counterfactual_status = status_data.get('counterfactual', {}).get('status')
    
    # Determine methodology
    if (flavordb_status in ["FAILED", "INVALID_SCHEMA", None] or 
        counterfactual_status in ["FAILED", "INVALID_SCHEMA", None]):
        methodology = "Correlational Analysis"
        proxy_source = "Recipe1M"
    else:
        methodology = "Causal Independence"
        proxy_source = None
    
    return {
        "status": "PENDING",
        "methodology": methodology,
        "proxy_source": proxy_source,
        "timestamp": datetime.utcnow().isoformat()
    }

def create_ratification_log(amendment_data: dict, output_path: Path) -> None:
    """
    Write the amendment log to the specified output path.
    
    Args:
        amendment_data: Dict containing status, methodology, proxy_source, timestamp
        output_path: Path where the amendment log should be written
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(amendment_data, f, indent=2)

def main():
    """
    Main entry point for T012b: Prepare Amendment Log.
    
    Reads data/download_status.json, applies logic, and writes data/amendment_log.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    verification_report_path = project_root / "data" / "download_status.json"
    amendment_log_path = project_root / "data" / "amendment_log.json"
    
    print("Starting T012b: Prepare Amendment Log...")
    
    try:
        # Check plan for amendment based on verification report
        amendment_data = check_plan_for_amendment(verification_report_path)
        
        # Create the ratification log
        create_ratification_log(amendment_data, amendment_log_path)
        
        print(f"Amendment log created successfully at: {amendment_log_path}")
        print(f"Methodology: {amendment_data['methodology']}")
        print(f"Proxy Source: {amendment_data['proxy_source']}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Create a failed status log if verification report is missing
        amendment_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log = {
            "status": "FAILED",
            "error": str(e),
            "methodology": None,
            "proxy_source": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(amendment_log_path, 'w') as f:
            json.dump(error_log, f, indent=2)
        raise
    except RuntimeError as e:
        print(f"Critical Error: {e}")
        # Pipeline halt - create failed log
        amendment_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log = {
            "status": "FAILED",
            "error": str(e),
            "methodology": None,
            "proxy_source": None,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(amendment_log_path, 'w') as f:
            json.dump(error_log, f, indent=2)
        raise

if __name__ == "__main__":
    main()