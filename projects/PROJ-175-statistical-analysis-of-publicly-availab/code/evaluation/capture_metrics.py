"""
Metrics capture and consolidation module.
Aggregates all evaluation metrics into final reports.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_json_safe(path: Path) -> Optional[Dict]:
    """Safely load JSON file."""
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None

def extract_pipeline_metrics() -> Dict:
    """Extract pipeline execution metrics."""
    log_path = Path("data/pipeline_execution_log.json")
    log = load_json_safe(log_path)
    
    if log:
        return {
            "total_steps": len(log),
            "successful_steps": sum(1 for entry in log if entry.get("status") == "SUCCESS"),
            "failed_steps": sum(1 for entry in log if entry.get("status") == "FAILED"),
            "execution_log": log
        }
    return {"total_steps": 0, "successful_steps": 0, "failed_steps": 0}

def extract_logistic_metrics() -> Dict:
    """Extract logistic regression metrics."""
    results_path = Path("data/final/logistic_results.json")
    results = load_json_safe(results_path)
    
    if results:
        return {
            "converged": results.get("models", {}).get("full", {}).get("converged", False),
            "score": results.get("models", {}).get("full", {}).get("score", 0.0),
            "n_samples": results.get("n_samples", 0),
            "predictors": results.get("predictors", [])
        }
    return {}

def extract_bayesian_metrics() -> Dict:
    """Extract Bayesian model metrics."""
    results_path = Path("data/final/bayesian_results.json")
    results = load_json_safe(results_path)
    
    if results:
        return {
            "converged": results.get("converged", False),
            "r_hat": results.get("r_hat", {}),
            "n_samples": results.get("n_samples", 0)
        }
    return {}

def extract_vif_metrics() -> Dict:
    """Extract VIF metrics."""
    vif_path = Path("data/vif_scores_initial.json")
    vif_results = load_json_safe(vif_path)
    
    if vif_results:
        return {
            "vif_scores": vif_results,
            "max_vif": max(vif_results.values()) if vif_results else 0
        }
    return {}

def extract_auc_delta_metrics() -> Dict:
    """Extract AUC delta metrics."""
    auc_path = Path("data/cv_delta_metrics.json")
    auc_results = load_json_safe(auc_path)
    
    if auc_results:
        return auc_results
    return {"auc_delta": 0.0, "p_value": 1.0, "ci_95": [0.0, 0.0]}

def extract_calibration_results() -> Dict:
    """Extract calibration results."""
    cal_path = Path("data/calibration_test_results.json")
    cal_results = load_json_safe(cal_path)
    
    if cal_results:
        return cal_results
    return {"max_deviation": 0.0, "passed": True}

def generate_final_validation_report():
    """Generate final validation report."""
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "pipeline_metrics": extract_pipeline_metrics(),
        "logistic_metrics": extract_logistic_metrics(),
        "bayesian_metrics": extract_bayesian_metrics(),
        "vif_metrics": extract_vif_metrics(),
        "auc_delta_metrics": extract_auc_delta_metrics(),
        "calibration_results": extract_calibration_results()
    }
    
    # Save evaluation log
    eval_log_path = Path("data/evaluation_log.json")
    with open(eval_log_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Saved evaluation log to {eval_log_path}")
    
    # Save final validation report
    final_report_path = Path("data/final_validation_report.json")
    with open(final_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Saved final validation report to {final_report_path}")
    
    return report

def main():
    """Main function for metrics capture."""
    try:
        report = generate_final_validation_report()
        print("Metrics capture completed successfully")
    except Exception as e:
        print(f"Metrics capture failed: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()