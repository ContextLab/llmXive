import os
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Ensure paths are correct relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RESULTS = PROJECT_ROOT / "data" / "results"
DATA_MODELS = PROJECT_ROOT / "data" / "models"

def load_json_file(path):
    """Utility to load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_model_metrics():
    """Loads model_metrics.json."""
    return load_json_file(DATA_RESULTS / "model_metrics.json")

def load_feature_importance_pvalues():
    """Loads feature importance p-values."""
    # Check for corrected or raw, prefer corrected
    corrected_path = DATA_RESULTS / "feature_importance_pvalues_corrected.json"
    raw_path = DATA_RESULTS / "feature_importance_pvalues_raw.json"
    
    if corrected_path.exists():
        return load_json_file(corrected_path)
    elif raw_path.exists():
        return load_json_file(raw_path)
    return {}

def load_stability_metrics():
    """Loads stability metrics."""
    return load_json_file(DATA_RESULTS / "stability_metrics.json")

def generate_interpretation_report(metrics, pvalues, stability):
    """
    Generates the final interpretation report.
    T025: Ensures the associational disclaimer is present.
    """
    report = {
        "generated_at": datetime.now().isoformat(),
        "model_performance": {
            "r2": metrics.get('r2'),
            "rmse": metrics.get('rmse'),
            "std_r2": metrics.get('std_r2'),
            "std_rmse": metrics.get('std_rmse')
        },
        "stability": stability,
        "feature_significance": pvalues,
        "disclaimer": metrics.get('disclaimer', 
            "Findings are associational due to observational data. "
            "No causal inference is made between gene expression, environmental factors, and VOC profiles."
        ),
        "analysis_type": "associational"
    }
    return report

def save_report(report, output_path):
    """Saves the report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Interpretation report saved to {output_path}")

def main():
    """
    Main entry point for report generation.
    """
    try:
        # Load dependencies
        metrics = load_model_metrics()
        pvalues = load_feature_importance_pvalues()
        stability = load_stability_metrics()
        
        # Generate report
        report = generate_interpretation_report(metrics, pvalues, stability)
        
        # Save
        output_path = DATA_RESULTS / "interpretation_report.json"
        save_report(report, output_path)
        
        print("Report generation completed.")
        
    except Exception as e:
        print(f"Error generating report: {e}")
        raise

if __name__ == "__main__":
    main()
