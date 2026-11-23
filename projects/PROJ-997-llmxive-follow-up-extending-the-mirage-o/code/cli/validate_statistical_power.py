"""
T040: Validate Statistical Power for Paired T-Test
--------------------------------------------------
Calculates the statistical power (1 - beta) for the paired t-test
performed in T027 (run_paired_mipu.py) given the observed effect size
and sample size.

If power < 0.8, logs a WARNING and prepares a "Power Analysis" section
to be appended to the final report (T033).
"""

import json
import logging
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORTS_DIR = PROJECT_ROOT / "docs" / "reports"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_paired_metrics(file_path: Path) -> Dict[str, Any]:
    """Load the paired MIPU metrics from T027."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required metrics file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def calculate_effect_size_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d for paired samples.
    d = mean(diff) / std(diff)
    """
    diffs = group1 - group2
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1) # Sample standard deviation
    
    if std_diff == 0:
        return 0.0
    
    return mean_diff / std_diff

def calculate_statistical_power(
    effect_size: float,
    sample_size: int,
    alpha: float = 0.05,
    tails: int = 2
) -> float:
    """
    Calculate statistical power for a paired t-test.
    Uses the non-central t-distribution approximation.
    """
    # Degrees of freedom
    df = sample_size - 1
    
    # Non-centrality parameter (nCP)
    # For paired t-test: nCP = d * sqrt(n)
    ncp = effect_size * np.sqrt(sample_size)
    
    # Critical t-value for the given alpha and df
    # Two-tailed test: split alpha
    critical_t = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability of rejecting the null hypothesis
    # when the alternative is true (non-central distribution)
    # Power = P(|T| > critical_t | nCP)
    #       = 1 - (CDF(critical_t) - CDF(-critical_t))
    
    power = 1 - (stats.nct.cdf(critical_t, df, ncp) - stats.nct.cdf(-critical_t, df, ncp))
    
    return power

def analyze_power(
    metrics: Dict[str, Any],
    alpha: float = 0.05
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Perform the full power analysis.
    Returns: (power, effect_size, analysis_details)
    """
    # Extract data
    if "acceptance_rate_proxy" not in metrics or "acceptance_rate_sync" not in metrics:
        raise ValueError("Metrics file missing required keys: 'acceptance_rate_proxy', 'acceptance_rate_sync'")
    
    proxy_rates = np.array(metrics["acceptance_rate_proxy"])
    sync_rates = np.array(metrics["acceptance_rate_sync"])
    
    if len(proxy_rates) != len(sync_rates):
        raise ValueError("Mismatched lengths in acceptance rates arrays.")
    
    n_samples = len(proxy_rates)
    
    if n_samples < 2:
        raise ValueError("Insufficient sample size for statistical power analysis (n < 2).")
    
    # Calculate effect size (Cohen's d for paired data)
    effect_size = calculate_effect_size_cohen_d(proxy_rates, sync_rates)
    
    # Calculate power
    power = calculate_statistical_power(effect_size, n_samples, alpha)
    
    analysis_details = {
        "sample_size": n_samples,
        "mean_diff_proxy": float(np.mean(proxy_rates)),
        "mean_diff_sync": float(np.mean(sync_rates)),
        "mean_difference": float(np.mean(proxy_rates - sync_rates)),
        "std_difference": float(np.std(proxy_rates - sync_rates, ddof=1)),
        "effect_size_cohen_d": float(effect_size),
        "alpha_threshold": alpha,
        "statistical_power": float(power),
        "power_adequate": power >= 0.8,
        "limitation_note": None
    }
    
    if power < 0.8:
        analysis_details["limitation_note"] = (
            f"Statistical power ({power:.4f}) is below the recommended threshold of 0.8. "
            f"This indicates a risk of Type II error (failing to detect a true effect). "
            f"The observed effect size (Cohen's d = {effect_size:.4f}) with n={n_samples} "
            f"may not be robust enough to support strong conclusions without further data collection."
        )
    
    return power, effect_size, analysis_details

def append_to_final_report(analysis_details: Dict[str, Any]) -> None:
    """
    Appends a 'Power Analysis' section to the final report (T033) if power is low.
    If the report doesn't exist yet, creates a placeholder note.
    """
    report_path = REPORTS_DIR / "001-llmxive-mipu-gap-bounds.md"
    
    section_content = f"""
## Power Analysis (T040)

- **Sample Size**: {analysis_details['sample_size']}
- **Observed Effect Size (Cohen's d)**: {analysis_details['effect_size_cohen_d']:.4f}
- **Statistical Power (1 - beta)**: {analysis_details['statistical_power']:.4f}
- **Adequacy**: {'Yes' if analysis_details['power_adequate'] else 'No (Below 0.8)'}
"""
    
    if analysis_details['limitation_note']:
        section_content += f"\n> **Limitation**: {analysis_details['limitation_note']}"
    
    section_content += "\n---\n"
    
    if report_path.exists():
        with open(report_path, 'a') as f:
            f.write(section_content)
        logger.info(f"Power analysis section appended to {report_path}")
    else:
        # If report doesn't exist, we can't append, but we log the warning
        logger.warning(f"Final report not found at {report_path}. Power analysis section could not be appended.")
        # Optionally create a standalone file for the analysis
        standalone_path = REPORTS_DIR / "001-llmxive-mipu-gap-bounds_power_analysis.md"
        with open(standalone_path, 'w') as f:
            f.write("# Power Analysis Report\n")
            f.write(section_content)
        logger.info(f"Power analysis saved to standalone file: {standalone_path}")

def main():
    parser = argparse.ArgumentParser(description="Validate statistical power for T027 paired t-test.")
    parser.add_argument(
        "--metrics-file",
        type=str,
        default=str(DATA_PROCESSED_DIR / "paired_mipu_metrics.json"),
        help="Path to the paired MIPU metrics JSON file."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level (alpha) for the test."
    )
    args = parser.parse_args()
    
    metrics_path = Path(args.metrics_file)
    
    try:
        logger.info(f"Loading metrics from {metrics_path}...")
        metrics = load_paired_metrics(metrics_path)
        
        logger.info("Calculating statistical power...")
        power, effect_size, details = analyze_power(metrics, args.alpha)
        
        # Output results to a JSON file for downstream consumption
        output_path = DATA_PROCESSED_DIR / "power_analysis_results.json"
        with open(output_path, 'w') as f:
            json.dump(details, f, indent=2)
        logger.info(f"Power analysis results saved to {output_path}")
        
        # Log summary
        status = "PASS" if details['power_adequate'] else "WARNING"
        logger.info(f"Power Analysis Result: {status} (Power: {power:.4f}, Effect Size: {effect_size:.4f})")
        
        if not details['power_adequate']:
            logger.warning(details['limitation_note'])
        
        # Append to final report if needed
        if not details['power_adequate']:
            append_to_final_report(details)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during power analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())