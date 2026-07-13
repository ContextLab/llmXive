import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_with_context
import statistics

logger = get_logger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file or return defaults."""
    default_config = {
        "data_dir": "data/processed",
        "results_dir": "data/processed",
        "high_dependency_threshold": 0.7,
        "model_name": "Qwen3-VL-4B-Instruct"
    }
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = json.load(f)
            default_config.update(user_config)
    
    return default_config

def load_held_out_test_set(test_set_path: str) -> List[Dict[str, Any]]:
    """Load the held-out test set containing state variables not in training coverage."""
    if not os.path.exists(test_set_path):
        raise FileNotFoundError(f"Held-out test set not found at {test_set_path}")
    
    with open(test_set_path, 'r') as f:
        return json.load(f)

def load_training_coverage_vectors(vectors_path: str) -> Dict[str, Any]:
    """Load the aggregated training coverage vectors."""
    if not os.path.exists(vectors_path):
        raise FileNotFoundError(f"Training coverage vectors not found at {vectors_path}")
    
    with open(vectors_path, 'r') as f:
        return json.load(f)

def load_experimental_logs(logs_path: str) -> List[Dict[str, Any]]:
    """Load the experimental logs from the State-Guided run."""
    if not os.path.exists(logs_path):
        raise FileNotFoundError(f"Experimental logs not found at {logs_path}")
    
    with open(logs_path, 'r') as f:
        return json.load(f)

def identify_high_state_dependency_apps(
    held_out_set: List[Dict[str, Any]],
    training_vectors: Dict[str, Any],
    threshold: float = 0.7
) -> List[str]:
    """
    Identify apps in the held-out set that have high state dependency.
    
    State dependency is calculated by comparing the held-out state variables
    against the training coverage vector. If a held-out variable is highly
    correlated with the training vector (or if the app's state changes
    significantly relative to the training baseline), it is considered
    high dependency.
    
    For this implementation, we calculate a dependency score based on the
    proportion of held-out variables that are present in the training vector.
    """
    training_coverage = training_vectors.get("coverage_vector", {})
    training_keys = set(training_coverage.keys())
    
    high_dependency_apps = []
    
    for app in held_out_set:
        app_id = app.get("app_id", "unknown")
        held_out_vars = app.get("state_variables", [])
        
        if not held_out_vars:
            continue
        
        # Calculate overlap ratio
        held_out_set_vars = set(held_out_vars)
        overlap = held_out_set_vars.intersection(training_keys)
        
        if len(held_out_vars) > 0:
            overlap_ratio = len(overlap) / len(held_out_vars)
        else:
            overlap_ratio = 0.0
        
        # If overlap is high, it suggests the app relies heavily on states
        # that were covered during training, indicating high state dependency
        if overlap_ratio >= threshold:
            high_dependency_apps.append(app_id)
            logger.info(f"App {app_id} identified as high state dependency (ratio: {overlap_ratio:.2f})")
    
    return high_dependency_apps

def extract_success_rates(
    logs: List[Dict[str, Any]],
    app_ids: List[str]
) -> Dict[str, List[float]]:
    """
    Extract success rates for specific apps from the experimental logs.
    
    Returns a dictionary mapping app_id to a list of success rates
    across multiple runs/batches.
    """
    app_success_rates: Dict[str, List[float]] = {app_id: [] for app_id in app_ids}
    
    for log_entry in logs:
        entry_app_id = log_entry.get("app_id")
        success_rate = log_entry.get("success_rate")
        
        if entry_app_id in app_ids and success_rate is not None:
            app_success_rates[entry_app_id].append(success_rate)
    
    # Filter out apps that had no data
    return {k: v for k, v in app_success_rates.items() if v}

def calculate_variance(success_rates: List[float]) -> float:
    """Calculate the variance of a list of success rates."""
    if len(success_rates) < 2:
        logger.warning(f"Insufficient data points ({len(success_rates)}) to calculate variance. Returning 0.0.")
        return 0.0
    
    return statistics.variance(success_rates)

def evaluate_transfer_performance(
    held_out_set: List[Dict[str, Any]],
    training_vectors: Dict[str, Any],
    experimental_logs: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate transfer performance, specifically focusing on variance
    across high state-dependency apps.
    """
    threshold = config.get("high_dependency_threshold", 0.7)
    
    # 1. Identify high state-dependency apps
    high_dep_apps = identify_high_state_dependency_apps(
        held_out_set, 
        training_vectors, 
        threshold
    )
    
    if not high_dep_apps:
        logger.warning("No high state-dependency apps found. Variance calculation skipped.")
        return {
            "high_dependency_apps": [],
            "variance_by_app": {},
            "overall_variance": 0.0,
            "message": "No high dependency apps identified."
        }
    
    # 2. Extract success rates for these apps
    success_rates_by_app = extract_success_rates(experimental_logs, high_dep_apps)
    
    if not success_rates_by_app:
        logger.warning("No success rate data found for high dependency apps.")
        return {
            "high_dependency_apps": high_dep_apps,
            "variance_by_app": {},
            "overall_variance": 0.0,
            "message": "No success rate data available."
        }
    
    # 3. Calculate variance for each app
    variance_by_app = {}
    all_success_rates = []
    
    for app_id, rates in success_rates_by_app.items():
        var = calculate_variance(rates)
        variance_by_app[app_id] = {
            "variance": var,
            "mean": statistics.mean(rates),
            "count": len(rates),
            "rates": rates
        }
        all_success_rates.extend(rates)
    
    # 4. Calculate overall variance across all high-dependency app runs
    overall_variance = calculate_variance(all_success_rates) if len(all_success_rates) >= 2 else 0.0
    
    return {
        "high_dependency_apps": high_dep_apps,
        "variance_by_app": variance_by_app,
        "overall_variance": overall_variance,
        "total_runs_analyzed": len(all_success_rates),
        "threshold_used": threshold
    }

def analyze_transfer_robustness(results: Dict[str, Any]) -> str:
    """
    Analyze the robustness of transfer based on variance results.
    Returns a human-readable summary string.
    """
    if not results.get("variance_by_app"):
        return "Unable to analyze robustness: insufficient data."
    
    overall_var = results.get("overall_variance", 0.0)
    app_count = len(results["variance_by_app"])
    
    # Interpretation logic
    if overall_var < 0.01:
        robustness = "HIGH"
        comment = "Very stable transfer performance across high-dependency apps."
    elif overall_var < 0.05:
        robustness = "MODERATE"
        comment = "Acceptable variance, but some instability detected."
    else:
        robustness = "LOW"
        comment = "High variance indicates unstable transfer for state-dependent tasks."
    
    summary = (
        f"Transfer Robustness Analysis: {robustness}\n"
        f"Overall Variance: {overall_var:.4f}\n"
        f"Apps Analyzed: {app_count}\n"
        f"Comment: {comment}"
    )
    
    return summary

def save_transfer_results(results: Dict[str, Any], output_path: str) -> None:
    """Save the transfer analysis results to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Transfer results saved to {output_path}")

def main():
    """Main entry point for the transfer analysis script."""
    config_path = os.environ.get("CONFIG_PATH", "data/processed/config.json")
    config = load_config(config_path)
    
    data_dir = Path(config["data_dir"])
    results_dir = Path(config["results_dir"])
    
    held_out_path = data_dir / "held_out_test_set.json"
    vectors_path = data_dir / "coverage_vectors.json"
    logs_path = data_dir / "experimental_logs.json"
    output_path = results_dir / "transfer_variance_analysis.json"
    
    logger.info("Starting Transfer Variance Analysis (T035)...")
    
    try:
        held_out_set = load_held_out_test_set(str(held_out_path))
        training_vectors = load_training_coverage_vectors(str(vectors_path))
        experimental_logs = load_experimental_logs(str(logs_path))
        
        results = evaluate_transfer_performance(
            held_out_set,
            training_vectors,
            experimental_logs,
            config
        )
        
        robustness_summary = analyze_transfer_robustness(results)
        logger.info(f"\n{robustness_summary}")
        
        # Add summary to results for saving
        results["robustness_summary"] = robustness_summary
        
        save_transfer_results(results, str(output_path))
        
        logger.info("T035 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()