"""
Statistical evaluation of model performance against baseline.

Performs paired t-tests of Random Forest and Gradient Boosting models
against the mean baseline, applying Bonferroni correction.

Output: results/metrics.json with corrected p-values and significance flags.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.metrics import paired_t_test, bonferroni_correct
from config import get_config, log_event, setup_logging

def setup_logger():
    """Setup logging for this module."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def load_model_predictions(results_dir: Path) -> Dict[str, Dict[str, List[float]]]:
    """
    Load predicted and actual values from the model evaluation results.
    
    Expects results from 02_train_models.py which should have saved
    predictions for RF, GB, and Mean Baseline models.
    
    Returns:
        Dict mapping model_name to {'pred': List[float], 'actual': List[float]}
    """
    metrics_path = results_dir / "model_predictions.json"
    if not metrics_path.exists():
        # Fallback: try to load from a generic results file if naming differs
        # This handles cases where 02_train_models.py might save to a different key
        logger = setup_logger()
        logger.warning(f"Predictions file {metrics_path} not found. "
                     "This script expects 02_train_models.py to have run first.")
        raise FileNotFoundError(
            f"Model predictions file not found at {metrics_path}. "
            "Ensure 02_train_models.py has been executed successfully."
        )
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    return data

def perform_statistical_tests(
    predictions: Dict[str, Dict[str, List[float]]],
    n_models: int = 2
) -> Dict[str, Any]:
    """
    Perform paired t-tests against the baseline and apply Bonferroni correction.
    
    Args:
        predictions: Dict with model names as keys and pred/actual lists as values.
        n_models: Number of primary models being tested (RF, GB). Excludes control analysis.
    
    Returns:
        Dictionary containing test results, corrected p-values, and significance flags.
    """
    logger = setup_logger()
    
    baseline_name = "MeanBaseline"
    models_to_test = ["RandomForest", "GradientBoosting"]
    
    # Validate that baseline and models exist in predictions
    if baseline_name not in predictions:
        raise ValueError(f"Baseline model '{baseline_name}' not found in predictions.")
    
    for model in models_to_test:
        if model not in predictions:
            raise ValueError(f"Model '{model}' not found in predictions.")
    
    baseline_actual = predictions[baseline_name]['actual']
    baseline_pred = predictions[baseline_name]['pred']
    
    results = {
        "alpha": 0.05,
        "n_models": n_models,
        "alpha_corrected": 0.05 / n_models,
        "tests": []
    }
    
    for model_name in models_to_test:
        model_pred = predictions[model_name]['pred']
        model_actual = predictions[model_name]['actual']
        
        # Ensure lengths match
        if len(model_pred) != len(baseline_pred):
            logger.warning(
                f"Length mismatch for {model_name} vs baseline. "
                f"Model: {len(model_pred)}, Baseline: {len(baseline_pred)}. "
                "Truncating to shortest length."
            )
            min_len = min(len(model_pred), len(baseline_pred), len(model_actual), len(baseline_actual))
            model_pred = model_pred[:min_len]
            model_actual = model_actual[:min_len]
            baseline_pred = baseline_pred[:min_len]
            baseline_actual = baseline_actual[:min_len]
        
        # Paired t-test: model vs baseline
        # We test if the model's error is significantly different from baseline's error
        # Error = |pred - actual|
        model_errors = [abs(p - a) for p, a in zip(model_pred, model_actual)]
        baseline_errors = [abs(p - a) for p, a in zip(baseline_pred, baseline_actual)]
        
        t_stat, p_value = paired_t_test(model_errors, baseline_errors)
        
        results["tests"].append({
            "model": model_name,
            "t_statistic": t_stat,
            "raw_p_value": p_value,
            "corrected_p_value": p_value, # Will be corrected below
            "is_significant": False # Will be set below
        })
    
    # Apply Bonferroni correction to all p-values
    raw_p_values = [test["raw_p_value"] for test in results["tests"]]
    corrected_p_values = bonferroni_correct(raw_p_values, n_models)
    
    # Update results with corrected p-values and significance flags
    for i, test in enumerate(results["tests"]):
        test["corrected_p_value"] = corrected_p_values[i]
        test["is_significant"] = corrected_p_values[i] < results["alpha_corrected"]
    
    return results

def save_metrics(results: Dict[str, Any], output_path: Path):
    """Save the statistical evaluation results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    setup_logger().info(f"Saved statistical evaluation results to {output_path}")

def main():
    """Main entry point for statistical evaluation."""
    logger = setup_logger()
    config = get_config()
    
    results_dir = Path(config.get("DATA_PATH", "data")) / "results"
    output_file = results_dir / "metrics.json"
    
    log_event("statistical_evaluation_start", {"output": str(output_file)})
    
    try:
        # Load predictions from previous step
        predictions = load_model_predictions(results_dir)
        
        # Perform statistical tests
        results = perform_statistical_tests(predictions, n_models=2)
        
        # Save results
        save_metrics(results, output_file)
        
        log_event("statistical_evaluation_complete", {
            "alpha_corrected": results["alpha_corrected"],
            "significant_models": [
                t["model"] for t in results["tests"] if t["is_significant"]
            ]
        })
        
        print(f"Statistical evaluation complete. Results saved to {output_file}")
        print(f"Alpha (corrected): {results['alpha_corrected']}")
        print("Results:")
        for test in results["tests"]:
            status = "SIGNIFICANT" if test["is_significant"] else "not significant"
            print(f"  {test['model']}: p={test['corrected_p_value']:.4f} ({status})")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        log_event("statistical_evaluation_failed", {"reason": str(e)})
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during statistical evaluation: {e}")
        log_event("statistical_evaluation_failed", {"reason": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()