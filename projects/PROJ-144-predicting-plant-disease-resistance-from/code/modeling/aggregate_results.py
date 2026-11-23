"""
T024: Aggregate Results for User Story 2.

This task reads the outputs of T020c, T021a, T021b, T021d, and T022
and aggregates them into a single canonical file: results/shap_analysis.json.

Note: T024 is the sole writer of results/shap_analysis.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure project root is in path if running from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "results"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents as a dictionary."""
    if not file_path.exists():
        logger.error(f"Required input file not found: {file_path}")
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error reading {file_path}: {e}")
        return None


def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """Save a dictionary to a JSON file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        logger.info(f"Successfully wrote output to: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write output to {file_path}: {e}")
        return False


def aggregate_metrics(
    feature_importance: Dict[str, Any],
    correlation_analysis: Dict[str, Any],
    model_validation: Dict[str, Any],
    sensitivity_analysis: Dict[str, Any],
    vif_scores: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all metrics into a single canonical structure.

    This function combines the outputs from:
    - T020c: Feature Importance Ranking
    - T021a: Correlation Analysis (Raw)
    - T021b: Model Validation (Hold-out/Permutation)
    - T021d: Sensitivity Analysis
    - T022: VIF Scores (Collinearity)

    The resulting structure is designed to be the canonical source for
    SHAP-like analysis summaries (even if actual SHAP values weren't computed,
    this file serves as the aggregated interpretability report).
    """
    aggregated = {
        "metadata": {
            "task_id": "T024",
            "description": "Aggregated results for Plant Disease Resistance Prediction",
            "generated_at": None  # Will be set by caller if needed, or left to default
        },
        "model_performance": {
            "balanced_accuracy": model_validation.get("balanced_accuracy"),
            "roc_auc": model_validation.get("roc_auc"),
            "permutation_p_value": model_validation.get("permutation_p_value"),
            "permutation_n": model_validation.get("permutation_n", 1000),
            "validation_method": model_validation.get("validation_method", "hold-out" if model_validation.get("holdout_indices") else "full")
        },
        "feature_importance": {
            "top_metabolites": feature_importance.get("top_metabolites", []),
            "method": feature_importance.get("method", "mean_decrease_impurity"),
            "total_features_analyzed": feature_importance.get("total_features", 0)
        },
        "correlation_analysis": {
            "significant_correlations": correlation_analysis.get("significant_correlations", []),
            "threshold_r": correlation_analysis.get("threshold_r", 0.4),
            "threshold_p": correlation_analysis.get("threshold_p", 0.01),
            "fdr_method": correlation_analysis.get("fdr_method", "benjamini_hochberg")
        },
        "sensitivity_analysis": {
            "thresholds": sensitivity_analysis.get("thresholds", []),
            "fpr_values": sensitivity_analysis.get("fpr_values", []),
            "fnr_values": sensitivity_analysis.get("fnr_values", []),
            "optimal_threshold": sensitivity_analysis.get("optimal_threshold")
        },
        "collinearity": {
            "vif_scores": vif_scores.get("vif_scores", {}),
            "high_collinearity_features": vif_scores.get("high_collinearity_features", []),
            "threshold_vif": vif_scores.get("threshold_vif", 5.0)
        }
    }

    # Add a summary section
    aggregated["summary"] = {
        "num_significant_correlations": len(correlation_analysis.get("significant_correlations", [])),
        "num_high_vif_features": len(vif_scores.get("high_collinearity_features", [])),
        "model_valid": model_validation.get("balanced_accuracy") is not None and model_validation.get("balanced_accuracy") > 0.5,
        "permutation_significant": model_validation.get("permutation_p_value", 1.0) < 0.05
    }

    return aggregated


def main():
    """
    Main entry point for T024.
    Reads all prerequisite artifacts and writes the aggregated result.
    """
    logger.info("Starting T024: Aggregate Results")

    # Define input paths
    input_paths = {
        "feature_importance": RESULTS_DIR / "feature_importance_ranking.json",
        "correlation_analysis": RESULTS_DIR / "correlation_analysis_raw.json",
        "model_validation": RESULTS_DIR / "model_validation.json",
        "sensitivity_analysis": RESULTS_DIR / "sensitivity_analysis.json",
        "vif_scores": RESULTS_DIR / "vif_scores.json"
    }

    # Output path
    output_path = RESULTS_DIR / "shap_analysis.json"

    # Load all inputs
    inputs = {}
    missing_files = []
    for key, path in input_paths.items():
        data = load_json_file(path)
        if data is None:
            missing_files.append(str(path))
        inputs[key] = data

    if missing_files:
        logger.error(f"Missing required input files: {missing_files}")
        logger.error("T024 cannot proceed without all prerequisite artifacts.")
        sys.exit(1)

    # Aggregate
    logger.info("Aggregating metrics...")
    aggregated_data = aggregate_metrics(
        feature_importance=inputs["feature_importance"],
        correlation_analysis=inputs["correlation_analysis"],
        model_validation=inputs["model_validation"],
        sensitivity_analysis=inputs["sensitivity_analysis"],
        vif_scores=inputs["vif_scores"]
    )

    # Save output
    if save_json_file(output_path, aggregated_data):
        logger.info("T024 completed successfully.")
        sys.exit(0)
    else:
        logger.error("T024 failed to write output.")
        sys.exit(1)


if __name__ == "__main__":
    main()
