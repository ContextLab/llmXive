"""
Statistical Report Generation Module for PolyPerme Project.

This module aggregates results from metrics, VIF analysis, and sensitivity sweeps
to generate a comprehensive final statistical report.
"""

import os
import sys
import logging
import json
from typing import Dict, Any, List, Optional
from data.utils import setup_logging

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVAL_RESULTS_DIR = os.path.join(PROJECT_ROOT, "code", "evaluation", "results")
PROCESSED_DATA_DIR = os.path.join(PROJECT_ROOT, "code", "data", "processed")

# Output paths
FINAL_REPORT_PATH = os.path.join(EVAL_RESULTS_DIR, "final_statistical_report.json")
METRICS_PATH = os.path.join(EVAL_RESULTS_DIR, "metrics.json")
VIF_PATH = os.path.join(EVAL_RESULTS_DIR, "vif_analysis.json")
SENSITIVITY_PATH = os.path.join(EVAL_RESULTS_DIR, "sensitivity_sweep.json")
WILCOXON_PATH = os.path.join(EVAL_RESULTS_DIR, "wilcoxon_results.json")


def load_metrics_from_json(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load model performance metrics from the metrics JSON file.

    Args:
        path: Optional path to the metrics file. Defaults to standard location.

    Returns:
        Dictionary containing model metrics (R2, MAE, Pearson, etc.) per model.
    """
    if path is None:
        path = METRICS_PATH

    if not os.path.exists(path):
        raise FileNotFoundError(f"Metrics file not found at {path}. "
                                "Run the evaluation pipeline first.")

    with open(path, 'r') as f:
        return json.load(f)


def load_vif_results(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Variance Inflation Factor (VIF) analysis results.

    Args:
        path: Optional path to the VIF JSON file. Defaults to standard location.

    Returns:
        Dictionary containing VIF scores and flags for descriptors.
    """
    if path is None:
        path = VIF_PATH

    if not os.path.exists(path):
        # If VIF analysis hasn't been run, return a placeholder structure
        # The final report will note that VIF analysis is pending
        return {
            "status": "not_found",
            "message": "VIF analysis file not found. Run stats.py to generate.",
            "flags": [],
            "scores": {}
        }

    with open(path, 'r') as f:
        return json.load(f)


def load_sensitivity_results(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load sensitivity analysis sweep results.

    Args:
        path: Optional path to the sensitivity JSON file. Defaults to standard location.

    Returns:
        Dictionary containing threshold sweeps and stability metrics.
    """
    if path is None:
        path = SENSITIVITY_PATH

    if not os.path.exists(path):
        raise FileNotFoundError(f"Sensitivity sweep file not found at {path}. "
                                "Run T034 sensitivity analysis first.")

    with open(path, 'r') as f:
        return json.load(f)


def load_wilcoxon_results(path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Wilcoxon signed-rank test results.

    Args:
        path: Optional path to the Wilcoxon JSON file. Defaults to standard location.

    Returns:
        Dictionary containing p-values and test statistics.
    """
    if path is None:
        path = WILCOXON_PATH

    if not os.path.exists(path):
        # If Wilcoxon hasn't been run, return a placeholder structure
        return {
            "status": "not_found",
            "message": "Wilcoxon test file not found. Run stats.py to generate.",
            "p_value": None,
            "statistic": None,
            "conclusion": "Pending"
        }

    with open(path, 'r') as f:
        return json.load(f)


def generate_final_report(
    metrics: Optional[Dict[str, Any]] = None,
    vif_results: Optional[Dict[str, Any]] = None,
    sensitivity_results: Optional[Dict[str, Any]] = None,
    wilcoxon_results: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate the final statistical report aggregating all analysis results.

    This report combines:
    1. Model performance metrics (R2, MAE, Pearson correlation)
    2. VIF analysis flags for multicollinearity
    3. Sensitivity analysis stability metrics
    4. Wilcoxon signed-rank test conclusions

    Args:
        metrics: Pre-loaded metrics dictionary (optional, will load from file if None)
        vif_results: Pre-loaded VIF results (optional, will load from file if None)
        sensitivity_results: Pre-loaded sensitivity results (optional, will load from file if None)
        wilcoxon_results: Pre-loaded Wilcoxon results (optional, will load from file if None)
        output_path: Optional path to save the report. Defaults to standard location.

    Returns:
        Complete report dictionary containing all aggregated results.
    """
    logger = logging.getLogger(__name__)

    # Load data if not provided
    if metrics is None:
        metrics = load_metrics_from_json()
    if vif_results is None:
        vif_results = load_vif_results()
    if sensitivity_results is None:
        sensitivity_results = load_sensitivity_results()
    if wilcoxon_results is None:
        wilcoxon_results = load_wilcoxon_results()

    # Construct the final report
    report = {
        "report_metadata": {
            "title": "PolyPerme Final Statistical Report",
            "description": "Comprehensive statistical validation of GNN vs Baseline models for polymer permeability prediction",
            "generated_by": "T035 - Statistical Report Generation",
            "source_files": {
                "metrics": METRICS_PATH,
                "vif": VIF_PATH,
                "sensitivity": SENSITIVITY_PATH,
                "wilcoxon": WILCOXON_PATH
            }
        },
        "model_performance": metrics,
        "vif_analysis": {
            "status": "completed" if vif_results.get("status") != "not_found" else "pending",
            "multicollinearity_flags": vif_results.get("flags", []),
            "descriptor_scores": vif_results.get("scores", {}),
            "conclusion": (
                "No significant multicollinearity detected" if not vif_results.get("flags")
                else f"Multicollinearity detected in {len(vif_results.get('flags', []))} descriptors"
            ) if vif_results.get("status") != "not_found" else "Analysis not yet performed"
        },
        "sensitivity_analysis": {
            "thresholds_tested": sensitivity_results.get("thresholds", []),
            "stability_metric": sensitivity_results.get("stability_metric", None),
            "successful_prediction_rates": {
                str(t): sensitivity_results.get("results", {}).get(str(t), {}).get("successful_prediction_rate")
                for t in sensitivity_results.get("thresholds", [])
            },
            "conclusion": (
                f"Model stability metric: {sensitivity_results.get('stability_metric', 'N/A'):.4f}. "
                "Lower values indicate more stable predictions across thresholds."
            ) if sensitivity_results.get("stability_metric") is not None else "Analysis not yet performed"
        },
        "statistical_significance": {
            "test_type": "Wilcoxon Signed-Rank Test",
            "comparison": "GNN vs Random Forest Baseline",
            "p_value": wilcoxon_results.get("p_value"),
            "statistic": wilcoxon_results.get("statistic"),
            "significance_level": 0.05,
            "conclusion": (
                "GNN performance is statistically significantly different from RF baseline"
                if wilcoxon_results.get("p_value") is not None and wilcoxon_results.get("p_value") < 0.05
                else "No statistically significant difference detected between GNN and RF baseline"
            ) if wilcoxon_results.get("p_value") is not None else "Analysis not yet performed"
        },
        "executive_summary": {
            "best_model": _identify_best_model(metrics),
            "statistical_validity": _determine_validity(metrics, vif_results, wilcoxon_results),
            "recommendations": _generate_recommendations(metrics, vif_results, sensitivity_results, wilcoxon_results)
        }
    }

    # Save to file
    if output_path is None:
        output_path = FINAL_REPORT_PATH

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Final statistical report generated and saved to {output_path}")
    return report


def _identify_best_model(metrics: Dict[str, Any]) -> str:
    """
    Identify the best performing model based on R2 score.

    Args:
        metrics: Dictionary of model metrics.

    Returns:
        Name of the best model.
    """
    if not metrics or "models" not in metrics:
        return "Unknown - No metrics available"

    models = metrics["models"]
    best_model = None
    best_r2 = -float('inf')

    for model_name, model_metrics in models.items():
        r2 = model_metrics.get("r2", -float('inf'))
        if r2 > best_r2:
            best_r2 = r2
            best_model = model_name

    if best_model is None:
        return "Unknown - No valid R2 scores"

    return f"{best_model} (R²={best_r2:.4f})"


def _determine_validity(metrics: Dict[str, Any], vif_results: Dict[str, Any], wilcoxon_results: Dict[str, Any]) -> str:
    """
    Determine the overall statistical validity of the results.

    Args:
        metrics: Model performance metrics.
        vif_results: VIF analysis results.
        wilcoxon_results: Wilcoxon test results.

    Returns:
        Summary string of validity status.
    """
    issues = []

    # Check for significant VIF issues
    if vif_results.get("flags") and vif_results.get("status") != "not_found":
        issues.append("Multicollinearity detected in baseline descriptors")

    # Check for statistical significance
    p_val = wilcoxon_results.get("p_value")
    if p_val is None and wilcoxon_results.get("status") == "not_found":
        issues.append("Wilcoxon significance test not performed")
    elif p_val is not None and p_val >= 0.05:
        issues.append("No statistically significant difference between models")

    # Check for reasonable R2 scores
    if metrics and "models" in metrics:
        max_r2 = max(m.get("r2", -1) for m in metrics["models"].values())
        if max_r2 < 0.2:
            issues.append("Model performance (R² < 0.2) indicates poor predictive capability")

    if not issues:
        return "Statistically valid: No major issues detected"
    else:
        return "Validity concerns: " + "; ".join(issues)


def _generate_recommendations(
    metrics: Dict[str, Any],
    vif_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    wilcoxon_results: Dict[str, Any]
) -> List[str]:
    """
    Generate actionable recommendations based on the analysis.

    Args:
        metrics: Model performance metrics.
        vif_results: VIF analysis results.
        sensitivity_results: Sensitivity analysis results.
        wilcoxon_results: Wilcoxon test results.

    Returns:
        List of recommendation strings.
    """
    recommendations = []

    # R2-based recommendations
    if metrics and "models" in metrics:
        for model_name, model_metrics in metrics["models"].items():
            r2 = model_metrics.get("r2", 0)
            if r2 < 0.3:
                recommendations.append(
                    f"Improve {model_name} model: R²={r2:.2f} is below acceptable threshold (0.3). "
                    "Consider feature engineering or hyperparameter tuning."
                )

    # VIF-based recommendations
    if vif_results.get("flags") and vif_results.get("status") != "not_found":
        recommendations.append(
            "Address multicollinearity: Remove or combine highly correlated descriptors "
            f"identified by VIF > 5: {vif_results['flags']}"
        )

    # Sensitivity-based recommendations
    stability = sensitivity_results.get("stability_metric")
    if stability is not None and stability > 0.1:
        recommendations.append(
            f"High prediction variability detected (stability metric={stability:.2f}). "
            "Consider ensemble methods or regularization to improve robustness."
        )

    # Wilcoxon-based recommendations
    p_val = wilcoxon_results.get("p_value")
    if p_val is not None and p_val < 0.05:
        recommendations.append(
            "The GNN model shows statistically significant improvement over the baseline. "
            "Proceed with GNN for production deployment."
        )
    elif p_val is not None:
        recommendations.append(
            "No significant difference between GNN and baseline. "
            "Consider simpler baseline models for deployment to reduce computational cost."
        )

    if not recommendations:
        recommendations.append("All metrics within acceptable ranges. No immediate actions required.")

    return recommendations


def main():
    """
    Main entry point for generating the final statistical report.
    """
    logger = setup_logging("T035_report_generation")
    logger.info("Starting final statistical report generation...")

    try:
        # Generate the report
        report = generate_final_report()

        # Print summary to console
        print("\n" + "="*60)
        print("FINAL STATISTICAL REPORT SUMMARY")
        print("="*60)
        print(f"Best Model: {report['executive_summary']['best_model']}")
        print(f"Validity Status: {report['executive_summary']['statistical_validity']}")
        print("\nRecommendations:")
        for i, rec in enumerate(report['executive_summary']['recommendations'], 1):
            print(f"  {i}. {rec}")
        print("="*60 + "\n")

        logger.info("Report generation completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())