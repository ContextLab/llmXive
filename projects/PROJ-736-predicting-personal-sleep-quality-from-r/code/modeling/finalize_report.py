import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from config import get_paths
from utils.logging import setup_logging, log_stage_complete

def verify_plot_file():
    # Placeholder for plot verification
    return True

def finalize_report():
    """Finalize the report with all paths and metadata."""
    paths = get_paths()
    report_path = os.path.join(paths['results'], 'ResultReport.json')
    
    if not os.path.exists(report_path):
        print("No report to finalize.")
        return
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    report["finalized_at"] = datetime.now().isoformat()
    report["paths"] = {k: str(v) for k, v in paths.items()}
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_stage_complete("Finalize", "Report finalized.")

def main():
    finalize_report()

if __name__ == "__main__":
    sys.exit(main())