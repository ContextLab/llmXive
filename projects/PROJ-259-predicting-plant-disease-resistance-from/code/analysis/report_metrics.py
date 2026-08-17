import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import get_artifacts_path
from analysis.modeling import load_split_data, detect_problem_type
from analysis.validation import compare_models, validate_null_baseline, save_validation_report
from analysis.permutation_test import run_permutation_test, calculate_p_value, save_holdout_metrics
from utils.logging import get_logger

logger = get_logger(__name__)

def load_model_metrics() -> Dict[str, Any]:
    """Load model performance metrics from the modeling pipeline artifacts."""
    metrics_path = get_artifacts_path() / "models" / "model_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found at {metrics_path}. "
                                "Run the modeling pipeline (T017) first.")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_null_comparison() -> Dict[str, Any]:
    """Load null model comparison results from validation artifacts."""
    validation_path = get_artifacts_path() / "reports" / "validation_report.json"
    if not validation_path.exists():
        raise FileNotFoundError(f"Validation report not found at {validation_path}. "
                                "Run the validation pipeline (T018) first.")
    
    with open(validation_path, 'r') as f:
        return json.load(f)

def run_permutation_on_holdout(n_permutations: int = 1000) -> Dict[str, Any]:
    """
    Run permutation testing on the hold-out set to generate model-level p-value.
    This implements the requirement for T022/T033 overlap.
    """
    logger.info("Starting permutation test on hold-out set...")
    
    # Load hold-out data
    split_data_path = get_artifacts_path() / "data" / "holdout"
    if not split_data_path.exists():
        raise FileNotFoundError(f"Hold-out data not found at {split_data_path}. "
                                "Run the split pipeline (T015) first.")
    
    # Run permutation test
    result = run_permutation_test(
        n_permutations=n_permutations,
        random_state=42
    )
    
    return result

def compile_metrics_report(
    cv_metrics: Dict[str, Any],
    holdout_metrics: Dict[str, Any],
    null_comparison: Dict[str, Any],
    permutation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """Compile all metrics into the final report structure."""
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "cv_metrics": cv_metrics,
        "holdout_metrics": holdout_metrics,
        "null_model_comparison": null_comparison,
        "permutation_test": {
            "n_permutations": permutation_result.get("n_permutations", 0),
            "p_value": permutation_result.get("p_value", None),
            "observed_metric": permutation_result.get("observed_metric", None),
            "null_distribution_mean": permutation_result.get("null_distribution_mean", None),
            "null_distribution_std": permutation_result.get("null_distribution_std", None)
        },
        "summary": {
            "cv_accuracy": cv_metrics.get("accuracy", None),
            "cv_auc": cv_metrics.get("auc", None),
            "cv_r2": cv_metrics.get("r2", None),
            "holdout_accuracy": holdout_metrics.get("accuracy", None),
            "holdout_auc": holdout_metrics.get("auc", None),
            "holdout_r2": holdout_metrics.get("r2", None),
            "null_baseline_accuracy": null_comparison.get("null_accuracy", None),
            "improvement_over_null": None,
            "permutation_p_value": permutation_result.get("p_value", None),
            "is_significant": False
        }
    }
    
    # Calculate improvement over null
    if report["summary"]["holdout_accuracy"] is not None and \
       report["summary"]["null_baseline_accuracy"] is not None:
        report["summary"]["improvement_over_null"] = \
            report["summary"]["holdout_accuracy"] - report["summary"]["null_baseline_accuracy"]
    
    # Determine significance
    if report["summary"]["permutation_p_value"] is not None:
        report["summary"]["is_significant"] = report["summary"]["permutation_p_value"] <= 0.05
    
    return report

def save_metrics_report(report: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """Save the compiled metrics report to disk."""
    if output_path is None:
        output_path = get_artifacts_path() / "reports" / "metrics.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Metrics report saved to {output_path}")
    return output_path

def generate_metrics_pipeline(
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Main pipeline function to generate the complete metrics report.
    
    This function:
    1. Loads CV metrics from modeling
    2. Loads null model comparison from validation
    3. Runs permutation test on hold-out set
    4. Compiles all into a final report
    5. Saves to artifacts/reports/metrics.json
    """
    logger.info("Starting metrics report generation pipeline...")
    
    # 1. Load CV metrics
    logger.info("Loading CV metrics...")
    try:
        cv_metrics = load_model_metrics()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # 2. Load null comparison
    logger.info("Loading null model comparison...")
    try:
        null_comparison = load_null_comparison()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # 3. Run permutation test on hold-out set
    logger.info("Running permutation test on hold-out set...")
    try:
        permutation_result = run_permutation_on_holdout(n_permutations=n_permutations)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    
    # 4. Compile report
    logger.info("Compiling metrics report...")
    # We need holdout metrics from the permutation result or modeling
    # Assuming modeling pipeline saved holdout metrics in model_metrics.json
    holdout_metrics = cv_metrics.get("holdout_metrics", {})
    if not holdout_metrics:
        # Fallback: try to load from separate file
        holdout_path = get_artifacts_path() / "models" / "holdout_metrics.json"
        if holdout_path.exists():
            with open(holdout_path, 'r') as f:
                holdout_metrics = json.load(f)
        else:
            holdout_metrics = {"accuracy": None, "auc": None, "r2": None}
    
    report = compile_metrics_report(
        cv_metrics=cv_metrics,
        holdout_metrics=holdout_metrics,
        null_comparison=null_comparison,
        permutation_result=permutation_result
    )
    
    # 5. Save report
    logger.info("Saving metrics report...")
    output_path = save_metrics_report(report)
    
    logger.info("Metrics report generation complete.")
    return report

def main():
    """CLI entry point for generating the metrics report."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate comprehensive metrics report")
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations for the hold-out test (default: 1000)"
    )
    
    args = parser.parse_args()
    
    try:
        report = generate_metrics_pipeline(n_permutations=args.n_permutations)
        print(f"Report generated successfully. Summary: {report['summary']}")
    except Exception as e:
        logger.error(f"Failed to generate metrics report: {e}")
        raise

if __name__ == "__main__":
    main()
