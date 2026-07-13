import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from config import get_paths
from utils.logging import setup_logging, log_stage_complete

def load_result_report():
    paths = get_paths()
    path = os.path.join(paths['results'], 'ResultReport.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_result_report(report: Dict[str, Any]):
    paths = get_paths()
    path = os.path.join(paths['results'], 'ResultReport.json')
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)

def generate_result_report():
    """Generate the final ResultReport.json."""
    paths = get_paths()
    
    # Load evaluation results
    eval_path = os.path.join(paths['results'], 'evaluation_results.json')
    eval_data = {}
    if os.path.exists(eval_path):
        with open(eval_path, 'r') as f:
            eval_data = json.load(f)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "pipeline_version": "1.0.0",
        "metrics": eval_data,
        "status": "completed"
    }
    
    save_result_report(report)
    return report

def main():
    report = generate_result_report()
    print(f"Report generated: {report}")

if __name__ == "__main__":
    main()
