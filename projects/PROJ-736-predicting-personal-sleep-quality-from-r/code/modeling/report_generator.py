"""
Report generation script.
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

def load_result_report(path: str) -> dict:
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_result_report(report: dict, path: str) -> None:
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def main() -> int:
    """
    Main entry point for report generation.
    """
    paths = get_paths()
    ensure_dirs(paths)
    
    report = {
        "pipeline_version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "status": "complete",
        "metrics": {},
        "notes": "Approximation used for permutation test due to CI constraints."
    }
    
    # Load train results
    train_path = os.path.join(paths["data_results"], "train_results.json")
    if os.path.exists(train_path):
        with open(train_path, 'r') as f:
            report["metrics"]["training"] = json.load(f)
    
    # Load eval results
    eval_path = os.path.join(paths["data_results"], "evaluation_results.json")
    if os.path.exists(eval_path):
        with open(eval_path, 'r') as f:
            report["metrics"]["evaluation"] = json.load(f)
    
    report_path = os.path.join(paths["data_results"], "ResultReport.json")
    save_result_report(report, report_path)
    
    print(f"Report generated: {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
