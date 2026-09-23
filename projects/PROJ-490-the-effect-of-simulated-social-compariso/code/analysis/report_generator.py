"""
Final report generation.

Implements:
- T030: Generate final report JSON
- T030a: Interpretation labeling logic
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from utils.logger import get_logger
from data.config import get_config

logger = get_logger(__name__)

def load_model_results() -> Dict[str, Any]:
    """Load regression coefficients and diagnostics."""
    config = get_config()
    processed_dir = Path(config["paths"]["data_processed"])
    
    coeffs = []
    diagnostics = {}
    
    coeffs_file = processed_dir / "regression_coefficients.csv"
    if coeffs_file.exists():
        import pandas as pd
        df = pd.read_csv(coeffs_file)
        coeffs = df.to_dict(orient="records")
    
    diag_file = processed_dir / "model_diagnostics.json"
    if diag_file.exists():
        with open(diag_file, 'r') as f:
            diagnostics = json.load(f)
    
    return {"coefficients": coeffs, "diagnostics": diagnostics}

def load_bootstrap_results() -> Dict[str, Any]:
    """Load bootstrap results."""
    config = get_config()
    processed_dir = Path(config["paths"]["data_processed"])
    bootstrap_file = processed_dir / "bootstrap_results.json"
    
    if not bootstrap_file.exists():
        return {}
    
    with open(bootstrap_file, 'r') as f:
        return json.load(f)

def load_sensitivity_results() -> Dict[str, Any]:
    """Load sensitivity results."""
    config = get_config()
    processed_dir = Path(config["paths"]["data_processed"])
    sensitivity_file = processed_dir / "final_report.json"  # Placeholder, will be overwritten
    
    # We'll construct this in generate_final_report
    return {}

def load_data_path() -> str:
    """Load data path decision."""
    config = get_config()
    state_dir = Path(config["paths"]["state"])
    decision_file = state_dir / "data_path_decision.yaml"
    
    if not decision_file.exists():
        return "unknown"
    
    import yaml
    with open(decision_file, 'r') as f:
        data = yaml.safe_load(f)
    
    return data.get("decision", "unknown")

def generate_final_report() -> Dict[str, Any]:
    """
    Generate final report JSON.
    
    Artifact: data/processed/final_report.json
    """
    model_results = load_model_results()
    bootstrap_results = load_bootstrap_results()
    data_path = load_data_path()
    
    # T030a: Interpretation labeling
    interpretation = "Empirical Association" if data_path == "real" else "Simulated Causal Effect"
    
    # Load sensitivity results (simplified)
    sensitivity_results = []
    config = get_config()
    processed_dir = Path(config["paths"]["data_processed"])
    sweep_file = processed_dir / "sensitivity_sweep_results.csv"
    if sweep_file.exists():
        import pandas as pd
        df = pd.read_csv(sweep_file)
        sensitivity_results = df.to_dict(orient="records")
    
    # Parameter recovery bias (if synthetic)
    parameter_recovery_bias = 0.0
    if data_path == "synthetic":
        from analysis.sensitivity import load_ground_truth_params, load_estimated_coefficients, calculate_parameter_recovery
        gt = load_ground_truth_params()
        est = load_estimated_coefficients()
        if gt and est:
            parameter_recovery_bias = calculate_parameter_recovery(est, gt)
    
    report = {
        "data_source_type": data_path,
        "model_coefficients": model_results["coefficients"],
        "bootstrap_ci_variance": bootstrap_results.get("ci_variance", 0.0),
        "parameter_recovery_bias": parameter_recovery_bias,
        "sensitivity_results": sensitivity_results,
        "stability_failed": not bootstrap_results.get("stability_achieved", True),
        "interpretation": interpretation
    }
    
    return report

def save_report(report: Dict[str, Any]) -> None:
    """Save report to disk."""
    config = get_config()
    processed_dir = Path(config["paths"]["data_processed"])
    output_file = processed_dir / "final_report.json"
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved final report to {output_file}")

def run_report_generation():
    """Run full report generation pipeline."""
    logger.info("Generating final report...")
    report = generate_final_report()
    save_report(report)
    return report

if __name__ == "__main__":
    run_report_generation()
