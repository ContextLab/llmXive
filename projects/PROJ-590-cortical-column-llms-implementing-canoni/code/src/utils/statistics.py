import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GRADIENT_LOG_PATH = "data/logs/gradient_norms.json"
ABLATION_RESULTS_PATH = "data/results/ablation_results.json"
SCALING_RESULTS_PATH = "data/results/scaling_results.json"

def load_gradient_norms(log_path: Optional[str] = None) -> Dict[str, List[float]]:
    """
    Load gradient norms from the JSON log file generated during training.
    
    Args:
        log_path: Path to the gradient norms JSON file. Defaults to 
                  'data/logs/gradient_norms.json'.
    
    Returns:
        Dictionary mapping model/layer names to lists of gradient norms.
    
    Raises:
        FileNotFoundError: If the log file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = log_path or GRADIENT_LOG_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Gradient log not found at {path}. "
                                "Ensure training has been run with log_gradient_norms enabled.")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded gradient norms from {path}")
    return data

def compare_gradient_stability(
    baseline_log_path: Optional[str] = None,
    microcircuit_log_path: Optional[str] = None,
    window_size: int = 10
) -> Dict[str, Any]:
    """
    Compare gradient stability between baseline and microcircuit models.
    
    Calculates variance and coefficient of variation (CV) of gradient norms
    over a sliding window to assess training stability.
    
    Args:
        baseline_log_path: Path to baseline gradient norms log.
        microcircuit_log_path: Path to microcircuit gradient norms log.
        window_size: Size of the sliding window for stability calculation.
    
    Returns:
        Dictionary containing stability metrics for both models.
    """
    baseline_data = load_gradient_norms(baseline_log_path)
    microcircuit_data = load_gradient_norms(microcircuit_log_path)
    
    def calculate_stability_metrics(gradient_data: Dict[str, List[float]], 
                                  window_size: int) -> Dict[str, float]:
        """Calculate variance and CV over sliding windows."""
        metrics = {}
        for layer_name, norms in gradient_data.items():
            if len(norms) < window_size:
                logger.warning(f"Insufficient data for {layer_name}: {len(norms)} < {window_size}")
                continue
            
            # Calculate rolling variance
            rolling_var = []
            rolling_cv = []
            for i in range(len(norms) - window_size + 1):
                window = norms[i:i + window_size]
                window_arr = np.array(window)
                var = np.var(window_arr)
                mean = np.mean(window_arr)
                cv = (np.std(window_arr) / mean) if mean > 0 else 0.0
                rolling_var.append(var)
                rolling_cv.append(cv)
            
            if rolling_var:
                metrics[layer_name] = {
                    "mean_variance": float(np.mean(rolling_var)),
                    "mean_cv": float(np.mean(rolling_cv)),
                    "total_steps": len(norms)
                }
        
        return metrics
    
    baseline_metrics = calculate_stability_metrics(baseline_data, window_size)
    microcircuit_metrics = calculate_stability_metrics(microcircuit_data, window_size)
    
    return {
        "baseline": baseline_metrics,
        "microcircuit": microcircuit_metrics,
        "window_size": window_size
    }

def compare_ablation_results(
    results_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compare results across different ablation configurations.
    
    Args:
        results_path: Path to ablation results JSON file. Defaults to
                    'data/results/ablation_results.json'.
    
    Returns:
        Dictionary containing comparative analysis of ablation configurations.
    """
    path = results_path or ABLATION_RESULTS_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ablation results not found at {path}")
    
    with open(path, 'r') as f:
        results = json.load(f)
    
    # Analyze performance vs. parameter count trade-off
    configs = results.get("configs", [])
    performance_metrics = {}
    
    for config in configs:
        name = config.get("name", "unknown")
        mae = config.get("metrics", {}).get("mae", float('inf'))
        params = config.get("parameters", 0)
        active_constraints = config.get("active_constraints", [])
        
        performance_metrics[name] = {
            "mae": mae,
            "parameters": params,
            "active_constraints": active_constraints,
            "efficiency_score": mae / params if params > 0 else float('inf')
        }
    
    # Find optimal configuration based on efficiency
    optimal = min(performance_metrics.items(), 
                 key=lambda x: x[1]["efficiency_score"])
    
    return {
        "performance_by_config": performance_metrics,
        "optimal_config": optimal[0],
        "optimal_efficiency": optimal[1]["efficiency_score"],
        "total_configs_analyzed": len(configs)
    }

def calculate_scaling_exponent(
    scaling_results_path: Optional[str] = None
) -> Dict[str, float]:
    """
    Calculate the scaling exponent from scaling study results.
    
    Fits a power law relationship: Performance ~ Parameter^exponent
    using log-log linear regression.
    
    Args:
        scaling_results_path: Path to scaling results JSON file. Defaults to
                            'data/results/scaling_results.json'.
    
    Returns:
        Dictionary containing the calculated scaling exponent and fit statistics.
    
    Raises:
        FileNotFoundError: If the scaling results file does not exist.
    """
    path = scaling_results_path or SCALING_RESULTS_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scaling results not found at {path}")
    
    with open(path, 'r') as f:
        results = json.load(f)
    
    configs = results.get("configs", [])
    if not configs:
        raise ValueError("No scaling configurations found in results")
    
    # Extract parameter counts and performance metrics
    param_counts = []
    performance_values = []
    
    for config in configs:
        params = config.get("parameters", 0)
        mae = config.get("metrics", {}).get("mae", float('inf'))
        
        if params > 0 and mae != float('inf'):
            param_counts.append(params)
            performance_values.append(mae)
    
    if len(param_counts) < 2:
        raise ValueError("Insufficient data points to calculate scaling exponent")
    
    # Log-log regression: log(Performance) = exponent * log(Parameters) + intercept
    log_params = np.log(np.array(param_counts))
    log_performance = np.log(np.array(performance_values))
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_params, log_performance)
    
    return {
        "scaling_exponent": float(slope),
        "r_squared": float(r_value ** 2),
        "p_value": float(p_value),
        "std_error": float(std_err),
        "data_points": len(param_counts),
        "interpretation": (
            "Sublinear" if slope < 0 else 
            "Linear" if abs(slope) < 0.1 else 
            "Superlinear"
        )
    }

def main():
    """
    Main entry point for statistics analysis.
    
    Runs comparative analyses if required data files exist, otherwise logs warnings.
    """
    print("Running statistics analysis...")
    
    # Check for gradient stability analysis
    if os.path.exists(GRADIENT_LOG_PATH):
        try:
            stability = compare_gradient_stability(
                baseline_log_path=GRADIENT_LOG_PATH,
                microcircuit_log_path=GRADIENT_LOG_PATH
            )
            print(f"Gradient stability analysis complete. "
                 f"Window size: {stability['window_size']}")
        except Exception as e:
            logger.error(f"Gradient stability analysis failed: {e}")
    else:
        logger.warning(f"Gradient log not found at {GRADIENT_LOG_PATH}. "
                     "Skipping gradient stability analysis.")
    
    # Check for ablation results
    if os.path.exists(ABLATION_RESULTS_PATH):
        try:
            ablation_comparison = compare_ablation_results()
            print(f"Ablation analysis complete. "
                 f"Optimal config: {ablation_comparison['optimal_config']}")
        except Exception as e:
            logger.error(f"Ablation analysis failed: {e}")
    else:
        logger.warning(f"Ablation results not found at {ABLATION_RESULTS_PATH}. "
                     "Skipping ablation analysis.")
    
    # Check for scaling results
    if os.path.exists(SCALING_RESULTS_PATH):
        try:
            scaling_analysis = calculate_scaling_exponent()
            print(f"Scaling analysis complete. "
                 f"Exponent: {scaling_analysis['scaling_exponent']:.4f} "
                 f"(R²: {scaling_analysis['r_squared']:.4f})")
        except Exception as e:
            logger.error(f"Scaling analysis failed: {e}")
    else:
        logger.warning(f"Scaling results not found at {SCALING_RESULTS_PATH}. "
                     "Skipping scaling analysis.")
    
    print("Statistics analysis finished.")

if __name__ == "__main__":
    main()