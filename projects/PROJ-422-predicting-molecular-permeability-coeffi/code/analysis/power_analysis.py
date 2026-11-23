import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: str) -> Dict[str, Any]:
    """Load metrics from the JSON file."""
    path = Path(metrics_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def calculate_noncentrality_parameter(cohen_d: float, n: int) -> float:
    """
    Calculate the non-centrality parameter (lambda) for the t-test.
    lambda = d * sqrt(n / 2) for paired t-test
    """
    return cohen_d * np.sqrt(n / 2)

def calculate_power(ncp: float, df: int, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a two-tailed t-test.
    Uses the non-central t-distribution.
    
    Args:
        ncp: Non-centrality parameter
        df: Degrees of freedom
        alpha: Significance level
    
    Returns:
        Power value (probability of rejecting null hypothesis)
    """
    # Critical t-value for two-tailed test
    from scipy import stats
    
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability that the t-statistic exceeds the critical value
    # under the alternative hypothesis (non-central t-distribution)
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)
    
    return float(power)

def run_power_analysis(cohen_d: float, n: int, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run post-hoc power analysis.
    
    Args:
        cohen_d: Observed effect size (Cohen's d)
        n: Sample size (number of paired observations)
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with power analysis results
    """
    if n < 2:
        raise ValueError("Sample size must be at least 2 for power analysis")
    
    df = n - 1  # Degrees of freedom for paired t-test
    ncp = calculate_noncentrality_parameter(cohen_d, n)
    power = calculate_power(ncp, df, alpha)
    
    # Interpret power level
    if power >= 0.8:
        interpretation = "Adequate"
    elif power >= 0.6:
        interpretation = "Moderate"
    else:
        interpretation = "Low"
    
    return {
        "power": round(power, 4),
        "effect_size_cohen_d": round(cohen_d, 4),
        "sample_size": n,
        "degrees_of_freedom": df,
        "alpha_level": alpha,
        "noncentrality_parameter": round(ncp, 4),
        "interpretation": interpretation,
        "power_threshold": 0.8,
        "notes": "Post-hoc power analysis based on observed effect size from paired t-test"
    }

def save_power_analysis(results: Dict[str, Any], output_path: str) -> None:
    """Save power analysis results to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis results saved to: {output_path}")

def main():
    """
    Main function to execute post-hoc power analysis.
    Reads from results/metrics.json and outputs to results/power_analysis.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    metrics_path = project_root / "results" / "metrics.json"
    output_path = project_root / "results" / "power_analysis.json"
    
    logger.info(f"Starting post-hoc power analysis")
    logger.info(f"Reading metrics from: {metrics_path}")
    
    try:
        # Load metrics
        metrics = load_metrics(str(metrics_path))
        
        # Extract required values
        if "cohen_d" not in metrics:
            raise KeyError("Cohen's d not found in metrics.json. Run T025 first.")
        
        # Determine sample size from prediction errors if available
        # Otherwise, use the number of test samples
        predictions_path = project_root / "results" / "predictions_errors.json"
        if predictions_path.exists():
            with open(predictions_path, 'r') as f:
                errors_data = json.load(f)
            
            # Get sample size from GNN errors (should be same for all models)
            if "gnn" in errors_data and "errors" in errors_data["gnn"]:
                n = len(errors_data["gnn"]["errors"])
            else:
                raise ValueError("Could not determine sample size from predictions_errors.json")
        else:
            # Fallback: try to infer from metrics or raise error
            raise FileNotFoundError(
                f"predictions_errors.json not found at {predictions_path}. "
                "Run T024 first to generate prediction errors."
            )
        
        cohen_d = metrics["cohen_d"]
        alpha = 0.05  # Standard significance level
        
        logger.info(f"Running power analysis with:")
        logger.info(f"  - Cohen's d: {cohen_d}")
        logger.info(f"  - Sample size: {n}")
        logger.info(f"  - Alpha level: {alpha}")
        
        # Run power analysis
        power_results = run_power_analysis(cohen_d, n, alpha)
        
        # Add metadata
        power_results["analysis_type"] = "post-hoc"
        power_results["test_type"] = "paired_t-test"
        power_results["comparison"] = "GNN vs Random Forest Baseline"
        
        # Save results
        save_power_analysis(power_results, str(output_path))
        
        logger.info(f"Power analysis completed successfully")
        logger.info(f"Power value: {power_results['power']} ({power_results['interpretation']})")
        
        return power_results
        
    except Exception as e:
        logger.error(f"Power analysis failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
