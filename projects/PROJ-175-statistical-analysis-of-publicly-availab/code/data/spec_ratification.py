import os
import sys
import json
from pathlib import Path
from datetime import datetime

def check_plan_for_amendment(amendment_path: Path) -> dict:
    """
    Checks if a ratified amendment exists in the project documentation.
    
    Args:
        amendment_path: Path to docs/amendment_record.md
        
    Returns:
        dict with 'exists' (bool) and 'status' (str or None)
    """
    if not amendment_path.exists():
        return {"exists": False, "status": None}
    
    # Read the markdown file to check for RATIFIED status
    try:
        content = amendment_path.read_text()
        # Simple check for RATIFIED status in the file content
        # A real implementation might parse YAML frontmatter or specific markers
        if "RATIFIED" in content.upper():
            return {"exists": True, "status": "RATIFIED"}
        elif "PENDING" in content.upper():
            return {"exists": True, "status": "PENDING"}
        else:
            return {"exists": True, "status": "UNKNOWN"}
    except Exception as e:
        return {"exists": True, "status": f"ERROR_READING: {str(e)}"}

def create_ratification_log(
    download_status_path: Path,
    amendment_log_path: Path,
    amendment_record_path: Path
) -> dict:
    """
    Creates the amendment log based on download status and amendment record.
    
    Logic:
    1. If recipe1m is FAILED, raise error (Pipeline Halt).
    2. If flavordb or counterfactual is FAILED/INVALID, check amendment record.
    3. If amendment record missing, create draft PENDING log and halt.
    4. If amendment record RATIFIED, set methodology to "Correlational Analysis".
    5. If all SUCCESS, set methodology to "Causal Independence".
    
    Returns:
        The generated log dictionary.
    """
    # Load download status
    if not download_status_path.exists():
        raise FileNotFoundError(f"Download status file not found: {download_status_path}")
        
    with open(download_status_path, 'r') as f:
        download_status = json.load(f)
    
    # Check Recipe1M status (Critical)
    recipe1m_status = download_status.get("recipe1m", {}).get("status")
    if recipe1m_status == "FAILED":
        raise RuntimeError("Pipeline Halt: Recipe1M download failed. Cannot proceed.")
    
    # Determine if we need an amendment
    flavordb_status = download_status.get("flavordb", {}).get("status", "SUCCESS")
    counterfactual_status = download_status.get("counterfactual", {}).get("status", "SUCCESS")
    
    needs_amendment = (
        flavordb_status in ["FAILED", "INVALID_SCHEMA"] or
        counterfactual_status in ["FAILED", "INVALID_SCHEMA"]
    )
    
    methodology = "Causal Independence"
    proxy_source = None
    log_status = "RATIFIED"  # Default if no amendment needed
    
    if needs_amendment:
        # Check for existing amendment record
        amendment_check = check_plan_for_amendment(amendment_record_path)
        
        if not amendment_check["exists"]:
            # Create draft PENDING log and halt
            log_status = "PENDING"
            methodology = "Correlational Analysis"
            proxy_source = "Recipe1M"
        elif amendment_check["status"] == "RATIFIED":
            log_status = "RATIFIED"
            methodology = "Correlational Analysis"
            proxy_source = "Recipe1M"
        else:
            # Pending or Unknown - halt
            log_status = "PENDING"
            methodology = "Correlational Analysis"
            proxy_source = "Recipe1M"
    else:
        # All sources successful
        methodology = "Causal Independence"
        proxy_source = None
        log_status = "RATIFIED"
    
    # Construct the log
    log_entry = {
        "status": log_status,
        "methodology": methodology,
        "proxy_source": proxy_source,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_status": {
            "recipe1m": recipe1m_status,
            "flavordb": flavordb_status,
            "counterfactual": counterfactual_status
        }
    }
    
    # Write the log
    amendment_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(amendment_log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return log_entry

def main():
    """Main entry point for T012b."""
    project_root = Path(__file__).resolve().parent.parent.parent
    download_status_path = project_root / "data" / "download_status.json"
    amendment_log_path = project_root / "data" / "amendment_log.json"
    amendment_record_path = project_root / "docs" / "amendment_record.md"
    
    try:
        log_entry = create_ratification_log(
            download_status_path,
            amendment_log_path,
            amendment_record_path
        )
        
        print(f"Amendment Log created successfully.")
        print(f"Status: {log_entry['status']}")
        print(f"Methodology: {log_entry['methodology']}")
        print(f"Proxy Source: {log_entry['proxy_source']}")
        
        # If status is PENDING, we simulate a halt by exiting with a specific code
        # or raising an error that the pipeline orchestrator can catch.
        if log_entry['status'] == 'PENDING':
            print("HOLD: Amendment pending human review. Pipeline halted.")
            sys.exit(1) # Non-zero exit to indicate halt
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"Critical Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
