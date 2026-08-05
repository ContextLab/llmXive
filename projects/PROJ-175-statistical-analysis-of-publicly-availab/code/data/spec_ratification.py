import os
import sys
import json
from pathlib import Path
from datetime import datetime

def check_plan_for_amendment(download_status_path: str) -> dict:
    """
    Reads data/download_status.json and determines the required methodology
    and proxy source based on the Critical Reframe logic.
    
    Logic:
    1. If recipe1m is "FAILED", raise error (Pipeline Halt).
    2. If flavordb or counterfactual is "FAILED" or "INVALID_SCHEMA",
       set methodology to "Correlational Analysis" and proxy_source to "Recipe1M".
    3. If all "SUCCESS", set methodology to "Causal Independence" and proxy_source to null.
    """
    if not os.path.exists(download_status_path):
        raise FileNotFoundError(f"Verification report not found: {download_status_path}. Run T012a first.")
    
    with open(download_status_path, 'r') as f:
        status_data = json.load(f)
    
    recipe1m_status = status_data.get('recipe1m', {}).get('status')
    flavordb_status = status_data.get('flavordb', {}).get('status')
    counterfactual_status = status_data.get('counterfactual', {}).get('status')
    
    # Critical Check: Recipe1M is mandatory
    if recipe1m_status == "FAILED":
        raise RuntimeError("Pipeline Halt: Recipe1M download failed. No proxy source available.")
    
    methodology = "Causal Independence"
    proxy_source = None
    
    # Check for fallback conditions
    if flavordb_status in ["FAILED", "INVALID_SCHEMA"] or counterfactual_status in ["FAILED", "INVALID_SCHEMA"]:
        methodology = "Correlational Analysis"
        proxy_source = "Recipe1M"
    
    return {
        "methodology": methodology,
        "proxy_source": proxy_source
    }

def create_ratification_log(amendment_path: str, methodology: str, proxy_source: str) -> None:
    """
    Writes the amendment log to data/amendment_log.json with status "PENDING".
    
    Output Schema:
    {
      "status": "PENDING",
      "methodology": str,
      "proxy_source": str | null,
      "timestamp": ISO8601
    }
    """
    log_data = {
        "status": "PENDING",
        "methodology": methodology,
        "proxy_source": proxy_source,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Ensure directory exists
    Path(amendment_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(amendment_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    download_status_path = project_root / "data" / "download_status.json"
    amendment_log_path = project_root / "data" / "amendment_log.json"
    
    try:
        # 1. Read status and determine logic
        decision = check_plan_for_amendment(str(download_status_path))
        
        # 2. Write the log (status remains PENDING for manual review or automated gate)
        create_ratification_log(
            str(amendment_log_path),
            decision["methodology"],
            decision["proxy_source"]
        )
        
        print(f"Amendment log created at {amendment_log_path}")
        print(f"Methodology: {decision['methodology']}")
        print(f"Proxy Source: {decision['proxy_source']}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Critical Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()