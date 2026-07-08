import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional

# Ensure project root is in path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.utils import setup_logging
from evaluation.metrics import compute_r2, compute_mae, compute_pearson_correlation
from evaluation.stats import wilcoxon_signed_rank_test, calculate_vif, sensitivity_analysis_sweep

logger = logging.getLogger(__name__)

def load_metrics_from_json(filepath: str) -> Dict[str, Any]:
    """
    Loads model metrics (GNN and Baselines) from a JSON report file.
    Expected structure:
    {
      "gnn": {"r2": float, "mae": float, "pearson": float, "predictions": [float], "true": [float]},
      "rf": {"r2": float, "mae": float, "pearson": float, "predictions": [float], "true": [float]},
      "linear": {"r2": float, "mae": float, "pearson": float}
    }
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_vif_results(filepath: str) -> Dict[str, float]:
    """
    Loads VIF results from the stats JSON file.
    Expected structure: {"vif_scores": {"feature_name": float, ...}}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"VIF results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
        return data.get("vif_scores", {})

def load_sensitivity_results(filepath: str) -> List[Dict[str, float]]:
    """
    Loads sensitivity analysis results.
    Expected structure: [{"threshold": float, "false_positive_rate": float, "true_positive_rate": float}, ...]
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sensitivity results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
        return data.get("sweep_results", [])

def generate_final_report(
    metrics_path: str = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/metrics.json",
    vif_path: str = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/vif_results.json",
    sensitivity_path: str = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/sensitivity_analysis.json",
    output_path: str = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/final_statistical_report.json"
) -> Dict[str, Any]:
    """
    Generates the final statistical report combining model performance,
    statistical significance tests (Wilcoxon), and multicollinearity flags (VIF).
    
    Args:
        metrics_path: Path to the model comparison metrics JSON.
        vif_path: Path to the VIF analysis JSON.
        sensitivity_path: Path to the sensitivity analysis JSON.
        output_path: Path where the final report will be saved.
    
    Returns:
        The final report dictionary.
    """
    logger.info(f"Loading metrics from {metrics_path}")
    metrics = load_metrics_from_json(metrics_path)
    
    logger.info(f"Loading VIF results from {vif_path}")
    vif_scores = load_vif_results(vif_path)
    
    logger.info(f"Loading sensitivity results from {sensitivity_path}")
    sensitivity_data = load_sensitivity_results(sensitivity_path)
    
    # Perform Wilcoxon signed-rank test on GNN vs RF
    # We need predictions and true values for both models
    gnn_preds = metrics.get("gnn", {}).get("predictions", [])
    gnn_true = metrics.get("gnn", {}).get("true", [])
    rf_preds = metrics.get("rf", {}).get("predictions", [])
    rf_true = metrics.get("rf", {}).get("true", [])
    
    wilcoxon_result = {"p_value": None, "statistic": None, "valid": False}
    
    if gnn_preds and gnn_true and rf_preds and rf_true:
        if len(gnn_true) == len(rf_true) and len(gnn_true) == len(gnn_preds) == len(rf_preds):
            # We compare errors: |pred - true|
            gnn_errors = [abs(g - t) for g, t in zip(gnn_preds, gnn_true)]
            rf_errors = [abs(r - t) for r, t in zip(rf_preds, rf_true)]
            
            try:
                stat, p_val = wilcoxon_signed_rank_test(gnn_errors, rf_errors)
                wilcoxon_result = {
                    "p_value": float(p_val),
                    "statistic": float(stat),
                    "valid": True,
                    "interpretation": "Significant difference" if p_val < 0.05 else "No significant difference"
                }
                logger.info(f"Wilcoxon test complete: p={p_val:.4f}")
            except Exception as e:
                logger.warning(f"Wilcoxon test failed: {e}")
                wilcoxon_result["error"] = str(e)
        else:
            logger.warning("Prediction/True arrays lengths do not match for Wilcoxon test.")
    else:
        logger.warning("Missing prediction data for Wilcoxon test.")

    # Determine VIF flags (high multicollinearity if VIF > 10)
    vif_flags = {
        "high_multicollinearity_detected": False,
        "flagged_features": []
    }
    
    for feature, score in vif_scores.items():
        if score > 10.0:
            vif_flags["high_multicollinearity_detected"] = True
            vif_flags["flagged_features"].append({
                "feature": feature,
                "vif_score": score
            })
    
    # Construct final report
    final_report = {
        "summary": {
            "gnn_performance": {
                "r2": metrics.get("gnn", {}).get("r2"),
                "mae": metrics.get("gnn", {}).get("mae"),
                "pearson": metrics.get("gnn", {}).get("pearson")
            },
            "rf_performance": {
                "r2": metrics.get("rf", {}).get("r2"),
                "mae": metrics.get("rf", {}).get("mae"),
                "pearson": metrics.get("rf", {}).get("pearson")
            },
            "wilcoxon_test": wilcoxon_result,
            "vif_analysis": vif_flags,
            "sensitivity_analysis_points": len(sensitivity_data)
        },
        "details": {
            "vif_scores": vif_scores,
            "sensitivity_sweep": sensitivity_data,
            "raw_metrics": metrics
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Final statistical report saved to {output_path}")
    return final_report

def main():
    """
    Entry point for generating the final statistical report.
    """
    setup_logging()
    
    # Default paths relative to project root
    metrics_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/metrics.json"
    vif_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/vif_results.json"
    sensitivity_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/sensitivity_analysis.json"
    output_path = "projects/PROJ-512-predicting-molecular-permeability-of-pol/code/evaluation/reports/final_statistical_report.json"
    
    # Allow overrides via environment variables
    metrics_path = os.environ.get("METRICS_PATH", metrics_path)
    vif_path = os.environ.get("VIF_PATH", vif_path)
    sensitivity_path = os.environ.get("SENSITIVITY_PATH", sensitivity_path)
    output_path = os.environ.get("OUTPUT_PATH", output_path)
    
    try:
        report = generate_final_report(
            metrics_path=metrics_path,
            vif_path=vif_path,
            sensitivity_path=sensitivity_path,
            output_path=output_path
        )
        print(json.dumps(report, indent=2))
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()