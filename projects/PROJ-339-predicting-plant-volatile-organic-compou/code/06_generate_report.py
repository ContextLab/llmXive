"""
T032: Generate final JSON report for model interpretation.

This script aggregates outputs from T028 (permutation importance),
T030 (FDR corrected p-values), T031 (overlap statistics), and T029 (SHAP)
to produce the final `data/results/interpretation_report.json`.

It includes the mandatory associational disclaimer and FDR values.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.hashing import compute_file_hash

def load_json_file(filepath: Path) -> dict:
    """Safely load a JSON file, returning empty dict if missing."""
    if not filepath.exists():
        print(f"Warning: {filepath} not found. Using empty data.")
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def main():
    # Define paths relative to project root
    data_dir = PROJECT_ROOT / "data"
    results_dir = data_dir / "results"
    models_dir = data_dir / "models"
    
    # Ensure output directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "interpretation_report.json"
    
    # Input artifacts from previous tasks
    model_path = models_dir / "random_forest.pkl"
    importance_path = results_dir / "feature_importance_pvalues.json"
    overlap_path = results_dir / "overlap_statistics.json"
    shap_path = results_dir / "shap_summary.png"
    
    # Load data from previous steps
    importance_data = load_json_file(importance_path)
    overlap_data = load_json_file(overlap_path)
    
    # Construct the final report
    report = {
        "report_type": "Model Interpretation",
        "model_source": str(model_path.relative_to(PROJECT_ROOT)),
        "timestamp": datetime.now().isoformat(),
        "disclaimer": (
            "Findings are associational due to observational data. "
            "Correlations identified do not imply causation. "
            "Results are derived from Random Forest regression with Nested k-Fold CV."
        ),
        "methodology": {
            "feature_importance": "Permutation Importance",
            "significance_correction": "Benjamini-Hochberg (FDR)",
            "biological_validation": "Overlap with known Terpene Synthase (TPS) families"
        },
        "results": {
            "top_features": [],
            "fdr_corrected_significance": {},
            "biological_overlap": overlap_data.get("overlap_summary", {}),
            "shap_visualization": str(shap_path.relative_to(PROJECT_ROOT)) if shap_path.exists() else None
        },
        "status": "Complete"
    }
    
    # Process top features if available
    if "features" in importance_data and "pvalues" in importance_data:
        features = importance_data["features"]
        pvalues = importance_data["pvalues"]
        # Assuming 'pvalues' are already FDR corrected as per T030
        # Create a list of dicts for top features
        feature_list = []
        for feat, p_val in zip(features, pvalues):
            feature_list.append({
                "feature": feat,
                "fdr_p_value": float(p_val),
                "significant": float(p_val) < 0.05
            })
        
        # Sort by p-value (ascending) to get most significant first
        feature_list.sort(key=lambda x: x["fdr_p_value"])
        report["results"]["top_features"] = feature_list[:20]  # Top 20
        report["results"]["fdr_corrected_significance"] = {
            "method": "Benjamini-Hochberg",
            "alpha": 0.05,
            "num_significant": sum(1 for f in feature_list if f["significant"])
        }
    
    # Handle overlap summary if present
    if overlap_data:
        if "overlap_summary" not in overlap_data:
            report["results"]["biological_overlap"] = overlap_data
        else:
            report["results"]["biological_overlap"] = overlap_data["overlap_summary"]
    
    # Compute hash of the report for reproducibility tracking
    report_hash = compute_file_hash(output_path) if output_path.exists() else None
    report["report_hash"] = report_hash
    
    # Write the final report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Successfully generated interpretation report: {output_path}")
    
    # Verify file exists
    if output_path.exists():
        final_hash = compute_file_hash(output_path)
        print(f"Report hash: {final_hash}")
    else:
        print("Error: Report file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
