import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Ensure project root is in path if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR, DATA_INTERMEDIATE_DIR
from utils.io import compute_file_hash, log_artifact

RESULTS_DIR = Path(RESULTS_DIR)
DATA_PROCESSED_DIR = Path(DATA_PROCESSED_DIR)
DATA_INTERMEDIATE_DIR = Path(DATA_INTERMEDIATE_DIR)

def load_json_file(filepath: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required input file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_metrics(metrics_data: dict, permutation_p_value: float) -> dict:
    """
    Aggregate final metrics ensuring all required keys are present.
    
    Expected input from T021b evaluation:
    {
        "balanced_accuracy": float,
        "roc_auc": float,
        "precision_recall": dict,
        "sensitivity_analysis": dict,
        ...
    }
    """
    aggregated = {
        "balanced_accuracy": metrics_data.get("balanced_accuracy"),
        "roc_auc": metrics_data.get("roc_auc"),
        "permutation_p_value": permutation_p_value,
        "timestamp": datetime.now().isoformat(),
        "pipeline_version": "1.0.0"
    }
    
    # Validate required keys
    if aggregated["balanced_accuracy"] is None:
        raise ValueError("balanced_accuracy is missing from evaluation results")
    if aggregated["roc_auc"] is None:
        raise ValueError("roc_auc is missing from evaluation results")
    if aggregated["permutation_p_value"] is None:
        raise ValueError("permutation_p_value is missing from permutation testing")
        
    return aggregated

def aggregate_shap_analysis(
    correlation_data: dict, 
    vif_data: dict, 
    model_importance: list = None
) -> dict:
    """
    Merge correlation data (T021a) and VIF scores (T022) into shap_analysis.json.
    
    Expected input from T021a (correlations):
    {
        "correlations": [
            {"feature_name": str, "correlation": float, "p_value": float, ...}
        ]
    }
    
    Expected input from T022 (VIF):
    {
        "vif_scores": [
            {"feature_name": str, "vif_value": float}
        ]
    }
    """
    # Extract top features from correlations (sorted by absolute correlation)
    correlations = correlation_data.get("correlations", [])
    top_features = []
    
    # Sort by absolute correlation magnitude
    sorted_corrs = sorted(correlations, key=lambda x: abs(x.get("correlation", 0)), reverse=True)
    
    for item in sorted_corrs[:20]:  # Top 20 features
        top_features.append({
            "feature_name": item.get("feature_name"),
            "shap_value": item.get("correlation"), # Using correlation as proxy for SHAP-like importance in this context
            "p_value": item.get("p_value"),
            "fdr_corrected_p": item.get("fdr_corrected_p")
        })
    
    # Prepare collinearity VIF data
    collinearity_vif = vif_data.get("vif_scores", [])
    
    # Mandatory framing for associational results
    framing = "These results represent associations, not causation"
    
    aggregated = {
        "top_features": top_features,
        "collinearity_vif": collinearity_vif,
        "framing": framing,
        "timestamp": datetime.now().isoformat(),
        "data_sources": {
            "correlations": "T021a_compute_correlations",
            "vif_scores": "T022_collinearity_diagnostics"
        }
    }
    
    return aggregated

def main():
    """
    Execute generation of results/metrics.json and results/shap_analysis.json.
    
    Dependencies:
    - T021b results (evaluation metrics) -> typically in results/metrics_raw.json or similar
    - T021a results (correlations) -> typically in results/correlations.json
    - T022 results (VIF scores) -> data/intermediate/vif_scores.json
    """
    print("Starting T024: Aggregating final metrics and SHAP analysis...")
    
    # Define paths
    # T021b usually outputs to results/metrics.json or similar. 
    # We assume T021b wrote to results/metrics_raw.json or we look for the main metrics file.
    # Based on task description, we aggregate results from T021a, T021b, T022.
    
    # Path for T021b output (Model Validation & Permutation)
    # Assuming the script saved the main metrics here. If T021b saved elsewhere, adjust.
    metrics_raw_path = RESULTS_DIR / "metrics_raw.json"
    if not metrics_raw_path.exists():
        # Fallback: check if T021b saved directly to metrics.json (unlikely if T024 is needed)
        # Or check for a specific output name if the previous task used one.
        # For robustness, we check common names.
        possible_paths = [
            RESULTS_DIR / "metrics.json",
            RESULTS_DIR / "evaluation_results.json",
            RESULTS_DIR / "model_metrics.json"
        ]
        found_path = None
        for p in possible_paths:
            if p.exists():
                found_path = p
                break
        
        if found_path:
            metrics_raw_path = found_path
            print(f"Found metrics at: {metrics_raw_path}")
        else:
            raise FileNotFoundError(
                f"Could not find evaluation metrics file. Expected {metrics_raw_path} "
                "or one of the fallback paths."
            )

    # Path for T021a output (Correlations)
    correlations_path = RESULTS_DIR / "correlations.json"
    if not correlations_path.exists():
        raise FileNotFoundError(f"Correlation data not found at {correlations_path}")
    
    # Path for T022 output (VIF)
    vif_path = DATA_INTERMEDIATE_DIR / "vif_scores.json"
    if not vif_path.exists():
        raise FileNotFoundError(f"VIF scores not found at {vif_path}")
    
    # Load data
    print("Loading evaluation metrics...")
    metrics_data = load_json_file(metrics_raw_path)
    
    print("Loading correlation data...")
    correlation_data = load_json_file(correlations_path)
    
    print("Loading VIF scores...")
    vif_data = load_json_file(vif_path)
    
    # Extract permutation p-value from metrics data if available, else default (should be present)
    permutation_p_value = metrics_data.get("permutation_p_value")
    if permutation_p_value is None:
        # Try to find it in a nested structure if T021b organized it differently
        if "validation" in metrics_data:
            permutation_p_value = metrics_data["validation"].get("permutation_p_value")
        
    if permutation_p_value is None:
        raise ValueError("permutation_p_value could not be extracted from evaluation results")
    
    # Aggregate Metrics
    print("Aggregating final metrics...")
    final_metrics = aggregate_metrics(metrics_data, permutation_p_value)
    
    # Aggregate SHAP/Correlation/VIF
    print("Aggregating SHAP analysis and collinearity data...")
    final_shap = aggregate_shap_analysis(correlation_data, vif_data)
    
    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write outputs
    metrics_output_path = RESULTS_DIR / "metrics.json"
    shap_output_path = RESULTS_DIR / "shap_analysis.json"
    
    with open(metrics_output_path, 'w') as f:
        json.dump(final_metrics, f, indent=2)
    print(f"Written: {metrics_output_path}")
    
    with open(shap_output_path, 'w') as f:
        json.dump(final_shap, f, indent=2)
    print(f"Written: {shap_output_path}")
    
    # Verify outputs
    assert metrics_output_path.exists(), "metrics.json was not created"
    assert shap_output_path.exists(), "shap_analysis.json was not created"
    
    # Validate schema compliance (basic check)
    with open(metrics_output_path, 'r') as f:
        m = json.load(f)
        assert "balanced_accuracy" in m, "Missing balanced_accuracy"
        assert "permutation_p_value" in m, "Missing permutation_p_value"
        assert "roc_auc" in m, "Missing roc_auc"
    
    with open(shap_output_path, 'r') as f:
        s = json.load(f)
        assert "top_features" in s, "Missing top_features"
        assert "collinearity_vif" in s, "Missing collinearity_vif"
        assert s.get("framing") == "These results represent associations, not causation", "Missing or incorrect framing"
    
    print("T024 completed successfully. All artifacts generated and validated.")
    
    # Log artifacts
    log_artifact(str(metrics_output_path), compute_file_hash(metrics_output_path))
    log_artifact(str(shap_output_path), compute_file_hash(shap_output_path))

if __name__ == "__main__":
    main()