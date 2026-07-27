import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FINAL_DIR = DATA_DIR / "final"
LOG_DIR = DATA_DIR / "logs"

def load_json_safe(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return None

def extract_pipeline_metrics() -> Dict:
    log_path = LOG_DIR / "pipeline_execution_log.json"
    data = load_json_safe(log_path)
    if not data:
        return {"status": "unknown", "steps": []}
    return {"status": "completed", "steps_count": len(data)}

def extract_logistic_metrics() -> Dict:
    path = FINAL_DIR / "logistic_results.json"
    return load_json_safe(path) or {}

def extract_bayesian_metrics() -> Dict:
    path = FINAL_DIR / "bayesian_results.json"
    return load_json_safe(path) or {}

def extract_vif_metrics() -> Dict:
    path = DATA_DIR / "vif_scores_initial.json"
    return load_json_safe(path) or {}

def extract_auc_delta_metrics() -> Dict:
    path = DATA_DIR / "auc_delta_metrics.json"
    return load_json_safe(path) or {}

def extract_calibration_results() -> Dict:
    path = DATA_DIR / "calibration_test_results.json"
    return load_json_safe(path) or {}

def generate_final_validation_report():
    """
    Aggregates all metrics into data/evaluation_log.json
    """
    print("Generating final validation report...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "pipeline": extract_pipeline_metrics(),
        "logistic_model": extract_logistic_metrics(),
        "bayesian_model": extract_bayesian_metrics(),
        "vif": extract_vif_metrics(),
        "auc_delta": extract_auc_delta_metrics(),
        "calibration": extract_calibration_results()
    }

    output_path = DATA_DIR / "evaluation_log.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Final validation report saved to {output_path}")

def main():
    generate_final_validation_report()

if __name__ == "__main__":
    import argparse
    main()