"""
Post-hoc power analysis for the molecular permeability prediction study.

This module implements statistical power analysis based on the observed effect size
(Cohen's d) from the paired t-test between GNN and RF-Baseline models.

It calculates the achieved power to interpret the reliability of the statistical
significance findings (SC-002, SC-002b, SC-002c).
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_metrics(metrics_path: Path) -> Dict[str, Any]:
    """
    Load the metrics JSON file containing t-test results and Cohen's d.
    
    Args:
        metrics_path: Path to results/metrics.json
        
    Returns:
        Dictionary containing metrics data
        
    Raises:
        FileNotFoundError: If the metrics file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
        
    with open(metrics_path, 'r') as f:
        return json.load(f)

def calculate_noncentrality_parameter(cohen_d: float, n: int) -> float:
    """
    Calculate the non-centrality parameter (ncp) for the t-distribution.
    
    The ncp is used to determine the power of the test.
    ncp = d * sqrt(n)
    
    Args:
        cohen_d: Cohen's d effect size
        n: Sample size
        
    Returns:
        Non-centrality parameter
    """
    return cohen_d * np.sqrt(n)

def calculate_power(
    ncp: float, 
    n: int, 
    alpha: float = 0.05, 
    alternative: str = 'two-sided'
) -> float:
    """
    Calculate statistical power using the non-central t-distribution.
    
    Power is the probability of correctly rejecting the null hypothesis
    when the alternative hypothesis is true.
    
    Args:
        ncp: Non-centrality parameter
        n: Sample size
        alpha: Significance level (default 0.05)
        alternative: Type of test ('two-sided', 'greater', 'less')
        
    Returns:
        Statistical power (probability between 0 and 1)
    """
    df = n - 1
    
    # Critical t-value for the given alpha and degrees of freedom
    if alternative == 'two-sided':
        crit_val = stats.t.ppf(1 - alpha/2, df)
        # Power is P(T > crit | H1) + P(T < -crit | H1)
        power = (1 - stats.nct.cdf(crit_val, df, ncp)) + stats.nct.cdf(-crit_val, df, ncp)
    elif alternative == 'greater':
        crit_val = stats.t.ppf(1 - alpha, df)
        power = 1 - stats.nct.cdf(crit_val, df, ncp)
    elif alternative == 'less':
        crit_val = stats.t.ppf(alpha, df)
        power = stats.nct.cdf(crit_val, df, ncp)
    else:
        raise ValueError(f"Unknown alternative: {alternative}")
        
    return float(power)

def run_power_analysis(
    cohen_d: float, 
    n: int, 
    alpha: float = 0.05, 
    alternative: str = 'two-sided'
) -> Dict[str, Any]:
    """
    Run the complete post-hoc power analysis.
    
    Args:
        cohen_d: Observed Cohen's d effect size
        n: Sample size (number of paired observations)
        alpha: Significance level
        alternative: Type of test
        
    Returns:
        Dictionary containing power analysis results
    """
    logger.info(f"Running power analysis with d={cohen_d:.4f}, n={n}, alpha={alpha}")
    
    # Calculate non-centrality parameter
    ncp = calculate_noncentrality_parameter(cohen_d, n)
    
    # Calculate power
    power = calculate_power(ncp, n, alpha, alternative)
    
    # Interpret power level
    if power >= 0.80:
        power_interpretation = "Adequate (>= 0.80)"
    elif power >= 0.60:
        power_interpretation = "Moderate (0.60 - 0.79)"
    else:
        power_interpretation = "Low (< 0.60)"
    
    results = {
        "power": round(power, 4),
        "effect_size_cohen_d": round(cohen_d, 4),
        "sample_size": n,
        "alpha_level": alpha,
        "alternative_test": alternative,
        "noncentrality_parameter": round(ncp, 4),
        "degrees_of_freedom": n - 1,
        "interpretation": power_interpretation,
        "sample_adequacy": "Sufficient" if power >= 0.80 else "Insufficient for robust inference"
    }
    
    logger.info(f"Power analysis complete: Power = {power:.4f} ({power_interpretation})")
    return results

def save_power_analysis(
    results: Dict[str, Any], 
    output_path: Path
) -> None:
    """
    Save power analysis results to a JSON file.
    
    Args:
        results: Power analysis results dictionary
        output_path: Path to save the JSON file
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Power analysis results saved to {output_path}")

def main() -> None:
    """
    Main entry point for post-hoc power analysis.
    
    This function:
    1. Loads metrics from results/metrics.json
    2. Extracts Cohen's d and sample size
    3. Runs power analysis
    4. Saves results to results/power_analysis.json
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    metrics_path = project_root / "results" / "metrics.json"
    output_path = project_root / "results" / "power_analysis.json"
    
    logger.info(f"Starting post-hoc power analysis")
    logger.info(f"Metrics path: {metrics_path}")
    logger.info(f"Output path: {output_path}")
    
    try:
        # Load metrics
        metrics = load_metrics(metrics_path)
        
        # Extract Cohen's d from paired t-test results
        # The structure depends on how T025 stored the data
        if "paired_ttest" in metrics:
            ttest_results = metrics["paired_ttest"]
            cohen_d = ttest_results.get("cohen_d")
            n = ttest_results.get("sample_size")
        elif "cohen_d" in metrics:
            cohen_d = metrics["cohen_d"]
            n = metrics.get("sample_size")
        else:
            # Try to find in model comparison section
            if "model_comparison" in metrics:
                comparison = metrics["model_comparison"]
                cohen_d = comparison.get("cohen_d")
                n = comparison.get("sample_size")
            else:
                raise KeyError("Could not find Cohen's d or sample_size in metrics file")
        
        if cohen_d is None:
            raise ValueError("Cohen's d not found in metrics. Ensure T025 completed successfully.")
        if n is None:
            raise ValueError("Sample size not found in metrics. Ensure T024/T025 completed successfully.")
        
        logger.info(f"Extracted Cohen's d: {cohen_d}, Sample size: {n}")
        
        # Run power analysis
        results = run_power_analysis(
            cohen_d=cohen_d,
            n=n,
            alpha=0.05,
            alternative='two-sided'
        )
        
        # Add metadata
        results["analysis_type"] = "post-hoc_power_analysis"
        results["linked_success_criteria"] = ["SC-002b", "SC-002c"]
        results["description"] = "Power analysis to interpret the reliability of the observed effect size and confidence intervals."
        
        # Save results
        save_power_analysis(results, output_path)
        
        logger.info("Post-hoc power analysis completed successfully")
        print(json.dumps(results, indent=2))
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in metrics file: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Missing required key in metrics: {e}")
        logger.error("Ensure T025 (paired t-test) has completed and populated metrics.json with Cohen's d and sample_size.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Value error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
