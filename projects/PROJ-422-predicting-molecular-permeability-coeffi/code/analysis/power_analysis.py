"""
Post-hoc power analysis implementation.
Calculates statistical power based on observed effect size (Cohen's d).
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Ensure parent directory is in path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

def load_metrics(metrics_path: Path) -> Dict[str, Any]:
    """Load metrics from the JSON file."""
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_noncentrality_parameter(cohen_d: float, n: int) -> float:
    """
    Calculate the non-centrality parameter (delta) for the t-distribution.
    delta = d * sqrt(n / 2) for paired t-test (approximation)
    """
    return cohen_d * np.sqrt(n / 2)

def calculate_power(delta: float, n: int, alpha: float = 0.05) -> float:
    """
    Calculate statistical power using the non-central t-distribution.
    Power = P(reject H0 | H1 is true)
    """
    dof = n - 1
    t_crit = stats.t.ppf(1 - alpha/2, dof)
    
    # Calculate power: probability that t-statistic exceeds critical value under H1
    # Using non-central t-distribution
    power = stats.nct.cdf(-t_crit, dof, delta) + (1 - stats.nct.cdf(t_crit, dof, delta))
    return float(power)

def run_power_analysis(metrics: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run power analysis based on metrics file contents.
    Expects 'statistical_test' -> 'cohens_d' and 'n_samples'.
    """
    if "statistical_test" not in metrics:
        raise ValueError("Metrics file must contain 'statistical_test' results.")
    
    stat_results = metrics["statistical_test"]
    cohen_d = stat_results.get("cohens_d")
    n_samples = stat_results.get("n_samples")
    
    if cohen_d is None or n_samples is None:
        raise ValueError("Missing 'cohens_d' or 'n_samples' in statistical_test results.")
    
    delta = calculate_noncentrality_parameter(cohen_d, n_samples)
    power = calculate_power(delta, n_samples, alpha)
    
    return {
        "effect_size_cohen_d": cohen_d,
        "sample_size": n_samples,
        "alpha_level": alpha,
        "noncentrality_parameter": delta,
        "statistical_power": power,
        "power_interpretation": "High" if power > 0.8 else "Medium" if power > 0.5 else "Low"
    }

def save_power_analysis(results: Dict[str, Any], output_path: Path) -> None:
    """Save power analysis results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Power analysis saved to {output_path}")

def main():
    """
    Main entry point for power analysis.
    Expects results/metrics.json to be populated by statistical_tests.py
    """
    logging.basicConfig(level=logging.INFO)
    
    base_path = Path(__file__).parent.parent.parent
    metrics_file = base_path / "results" / "metrics.json"
    output_file = base_path / "results" / "power_analysis.json"
    
    if not metrics_file.exists():
        logger.error(f"Metrics file not found: {metrics_file}")
        logger.error("Run code/analysis/statistical_tests.py first.")
        sys.exit(1)

    try:
        metrics = load_metrics(metrics_file)
        results = run_power_analysis(metrics)
        save_power_analysis(results, output_file)
        
        logger.info(f"Power: {results['statistical_power']:.4f} ({results['power_interpretation']})")

    except Exception as e:
        logger.error(f"Error during power analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()