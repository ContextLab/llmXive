"""
Finalize report script.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs

def verify_plot_file(path: str) -> bool:
    return os.path.exists(path)

def finalize_report() -> int:
    """
    Finalizes the report.
    """
    paths = get_paths()
    ensure_dirs(paths)
    
    report_path = os.path.join(paths["data_results"], "ResultReport.json")
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
        report["finalized"] = True
        report["finalized_at"] = datetime.now().isoformat()
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print("Report finalized.")
    else:
        print("No report to finalize.")
    return 0

def main() -> int:
    return finalize_report()

if __name__ == "__main__":
    sys.exit(main())