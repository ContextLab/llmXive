import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import get_artifacts_path
from analysis.modeling import load_split_data, train_model, train_null_model, evaluate_on_holdout
from analysis.permutation_test import run_permutation_test, calculate_p_value, save_holdout_metrics
from utils.logging import get_logger

logger = get_logger(__name__)

def load_model_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load model performance metrics from a JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Model metrics file not found: {metrics_path}")
    with open(metrics_path, 'r') as f:
        return json.load(f)

def load_null_comparison(null_metrics_path: Path) -> Dict[str, Any]:
    """Load null model comparison metrics from a JSON file."""
    if not null_metrics_path.exists():
        raise FileNotFoundError(f"Null model metrics file not found: {null_metrics_path}")
    with open(null_metrics_path, 'r') as f:
        return json.load(f)

def run_permutation_on_holdout(
    holdout_X: Any,
    holdout_y: Any,
    model: Any,
    metric_func: Any,
    n_permutations: int = 1000,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run permutation test on the hold-out set to generate a p-value.
    
    This calculates the probability that the model's performance on the
    hold-out set could be achieved by chance (shuffled labels).
    """
    logger.info(f"Running permutation test on hold-out set with {n_permutations} permutations")
    
    # Calculate observed metric
    observed_metric = metric_func(holdout_y, model.predict(holdout_X))
    
    # Run permutation test
    perm_metrics = []
    for i in range(n_permutations):
        # Shuffle labels
        y_permuted = holdout_y.sample(frac=1, random_state=random_state + i).reset_index(drop=True)
        perm_metric = metric_func(y_permuted, model.predict(holdout_X))
        perm_metrics.append(perm_metric)
    
    # Calculate p-value
    p_value = calculate_p_value(observed_metric, perm_metrics, higher_is_better=True)
    
    return {
        "observed_metric": float(observed_metric),
        "permuted_metrics_mean": float(np.mean(perm_metrics)),
        "permuted_metrics_std": float(np.std(perm_metrics)),
        "p_value": float(p_value),
        "n_permutations": n_permutations
    }

def compile_metrics_report(
    model_metrics: Dict[str, Any],
    null_comparison: Dict[str, Any],
    permutation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """Compile all metrics into a single report dictionary."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "model_performance": model_metrics,
        "null_model_comparison": null_comparison,
        "permutation_test": permutation_results,
        "summary": {
            "cv_accuracy": model_metrics.get("cv_accuracy"),
            "holdout_accuracy": model_metrics.get("holdout_accuracy"),
            "null_baseline_accuracy": null_comparison.get("accuracy"),
            "improvement_over_null": model_metrics.get("holdout_accuracy") - null_comparison.get("accuracy"),
            "permutation_p_value": permutation_results.get("p_value"),
            "statistically_significant": permutation_results.get("p_value", 1.0) < 0.05
        }
    }
    return report

def save_metrics_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save the metrics report to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Metrics report saved to {output_path}")

def generate_metrics_pipeline(
    split_data_path: Path,
    model_path: Path,
    null_metrics_path: Path,
    output_path: Path,
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Main pipeline to generate the metrics report.
    
    1. Load model metrics (CV accuracy, holdout accuracy)
    2. Load null model comparison
    3. Run permutation test on hold-out set
    4. Compile and save the final report
    """
    logger.info("Starting metrics report generation pipeline")
    
    # Load existing metrics
    try:
        model_metrics = load_model_metrics(model_path)
    except FileNotFoundError:
        logger.warning(f"Model metrics file not found at {model_path}. Running modeling pipeline first.")
        # If metrics don't exist, we need to run the modeling pipeline
        # This assumes the modeling pipeline has already been run and saved its outputs
        raise RuntimeError("Model metrics not found. Ensure modeling pipeline has been run.")
    
    try:
        null_comparison = load_null_comparison(null_metrics_path)
    except FileNotFoundError:
        logger.warning(f"Null model metrics file not found at {null_metrics_path}.")
        raise RuntimeError("Null model metrics not found. Ensure validation pipeline has been run.")
    
    # Load hold-out data for permutation test
    logger.info("Loading hold-out data for permutation test")
    # Assuming split data contains hold-out set
    # This needs to match the actual structure from split.py
    try:
        split_data = load_split_data(split_data_path)
        holdout_X = split_data.get("holdout_X")
        holdout_y = split_data.get("holdout_y")
        
        if holdout_X is None or holdout_y is None:
            raise ValueError("Hold-out data not found in split data file")
        
        # Load the trained model
        import pickle
        with open(model_path.with_suffix('.pkl'), 'rb') as f:
            model = pickle.load(f)
        
        # Define metric function (accuracy for classification)
        from sklearn.metrics import accuracy_score
        metric_func = accuracy_score
        
        # Run permutation test
        permutation_results = run_permutation_on_holdout(
            holdout_X, holdout_y, model, metric_func, n_permutations
        )
        
    except Exception as e:
        logger.error(f"Error running permutation test: {e}")
        # If permutation test fails, we still generate the report but with null p-value
        permutation_results = {
            "observed_metric": None,
            "permuted_metrics_mean": None,
            "permuted_metrics_std": None,
            "p_value": 1.0,  # Default to non-significant
            "n_permutations": n_permutations,
            "error": str(e)
        }
    
    # Compile final report
    report = compile_metrics_report(model_metrics, null_comparison, permutation_results)
    
    # Save report
    save_metrics_report(report, output_path)
    
    logger.info("Metrics report generation pipeline completed successfully")
    return report

def main():
    """Entry point for generating the metrics report."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate metrics report")
    parser.add_argument("--split-data", type=Path, required=True, help="Path to split data file")
    parser.add_argument("--model-metrics", type=Path, required=True, help="Path to model metrics file")
    parser.add_argument("--null-metrics", type=Path, required=True, help="Path to null model metrics file")
    parser.add_argument("--output", type=Path, required=True, help="Path to output metrics report")
    parser.add_argument("--n-permutations", type=int, default=1000, help="Number of permutations for test")
    
    args = parser.parse_args()
    
    try:
        generate_metrics_pipeline(
            args.split_data,
            args.model_metrics,
            args.null_metrics,
            args.output,
            args.n_permutations
        )
        print(f"Metrics report generated at {args.output}")
    except Exception as e:
        logger.error(f"Failed to generate metrics report: {e}")
        raise

if __name__ == "__main__":
    main()
