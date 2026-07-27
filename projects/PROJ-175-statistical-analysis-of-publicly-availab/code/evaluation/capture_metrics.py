"""
Metrics Capture Module
Consolidates all metrics into final validation report.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure parent is in path
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

def load_json_safe(path: Path) -> Optional[Dict]:
    """Load JSON file safely."""
    if not path.exists():
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None

def extract_pipeline_metrics(log_path: Path) -> Dict:
    """Extract pipeline execution metrics."""
    data = load_json_safe(log_path)
    if not data:
        return {"status": "UNKNOWN", "duration": 0}
    if isinstance(data, list):
        return data[-1] if data else {"status": "UNKNOWN"}
    return data

def extract_logistic_metrics(log_path: Path) -> Dict:
    """Extract logistic regression metrics."""
    return load_json_safe(log_path) or {}

def extract_bayesian_metrics(log_path: Path) -> Dict:
    """Extract Bayesian model metrics."""
    return load_json_safe(log_path) or {}

def extract_vif_metrics(log_path: Path) -> Dict:
    """Extract VIF metrics."""
    return load_json_safe(log_path) or {}

def extract_auc_delta_metrics(log_path: Path) -> Dict:
    """Extract AUC delta metrics."""
    return load_json_safe(log_path) or {}

def extract_lrt_vif_corrected(log_path: Path) -> Dict:
    """Extract LRT/VIF corrected metrics."""
    return load_json_safe(log_path) or {}

def extract_bayesian_convergence(log_path: Path) -> Dict:
    """Extract Bayesian convergence metrics."""
    return load_json_safe(log_path) or {}

def extract_vif_test_set(log_path: Path) -> Dict:
    """Extract VIF test set metrics."""
    return load_json_safe(log_path) or {}

def extract_calibration_results(log_path: Path) -> Dict:
    """Extract calibration results."""
    return load_json_safe(log_path) or {}

def generate_final_validation_report(output_path: Path):
    """Generate final validation report from all metrics."""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    report = {
        "pipeline": extract_pipeline_metrics(data_dir / "pipeline_execution_log.json"),
        "logistic": extract_logistic_metrics(data_dir / "final" / "logistic_results.json"),
        "bayesian": extract_bayesian_metrics(data_dir / "final" / "bayesian_results.json"),
        "vif": extract_vif_metrics(data_dir / "vif_scores_initial.json"),
        "auc_delta": extract_auc_delta_metrics(data_dir / "auc_delta_metrics.json"),
        "bayesian_convergence": extract_bayesian_convergence(data_dir / "bayesian_convergence_log.json"),
        "vif_test": extract_vif_test_set(data_dir / "vif_test_set.json"),
        "calibration": extract_calibration_results(data_dir / "calibration_test_results.json")
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def main():
    """Main entry point for metrics capture."""
    parser = argparse.ArgumentParser(description="Capture final metrics")
    parser.add_argument('--output', type=str, default='data/final_validation_report.json')
    args = parser.parse_args()
    
    output_path = Path(args.output)
    
    print("Generating final validation report...")
    generate_final_validation_report(output_path)
    
    print("Metrics capture completed successfully.")

if __name__ == "__main__":
    import argparse
    main()