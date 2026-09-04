import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Attempt to import statistical power analysis tools
# We prefer statsmodels for formal power analysis, but fallback to scipy if needed
try:
    from statsmodels.stats.power import TTestIndPower, GofChisquarePower
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    try:
        from scipy import stats
        HAS_SCIPY = True
    except ImportError:
        HAS_SCIPY = False

from config import get_config
from utils import setup_logging, PipelineError

logger = logging.getLogger(__name__)

def verify_imports():
    """Verify that required statistical libraries are available."""
    if not HAS_STATSMODELS and not HAS_SCIPY:
        raise PipelineError("Neither statsmodels nor scipy available for statistical power analysis.")
    return True

def load_analysis_data(input_path: Path) -> pd.DataFrame:
    """
    Load the analysis dataset containing retrieval results and metadata.
    Expected columns: planet_name, water_mixing_ratio, is_upper_limit, snr, resolution, temperature
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Analysis dataset not found at {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['water_mixing_ratio', 'is_upper_limit', 'snr', 'resolution']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in analysis dataset: {missing}")
    
    # Ensure boolean type for upper limit flag
    if 'is_upper_limit' in df.columns:
        df['is_upper_limit'] = df['is_upper_limit'].astype(bool)
    
    return df

def quality_control_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separate the dataset into resolved (detections) and censored (upper limits) subsets.
    This is crucial for power analysis as the effect size calculation differs.
    """
    detections = df[~df['is_upper_limit']].copy()
    censored = df[df['is_upper_limit']].copy()
    return detections, censored

def calculate_effect_size(detections: pd.DataFrame, target_tau: float = 0.3) -> float:
    """
    Calculate the effective effect size for power analysis.
    
    Since we are testing for a correlation (Kendall's tau) between water abundance 
    and temperature (or other variables), we convert the target tau to a Cohen's d 
    equivalent for a two-sample test (comparing high vs low temperature groups) 
    or use the tau directly if using a correlation-based power test.
    
    For this implementation, we estimate the effect size based on the variance 
    explained in the detected subset, normalized by the total variance.
    
    Args:
        detections: DataFrame with resolved water mixing ratios.
        target_tau: The target Kendall's tau effect size (0.3 per SC-004).
    
    Returns:
        float: Estimated effect size (Cohen's d equivalent).
    """
    if len(detections) < 2:
        return 0.0
    
    # Simple proxy: standard deviation of the mixing ratio relative to the mean
    # This is a rough estimate for power analysis in this context
    std_dev = detections['water_mixing_ratio'].std()
    mean_val = detections['water_mixing_ratio'].mean()
    
    if mean_val == 0:
        return 0.0
        
    # Cohen's d approximation (difference in means / pooled std dev)
    # Here we use the observed std dev as the noise floor
    effect_size = std_dev / abs(mean_val) if mean_val != 0 else 0.0
    
    # Cap at a reasonable maximum for sanity
    return min(effect_size, 2.0)

def calculate_statistical_power(
    df: pd.DataFrame, 
    effect_size: float = 0.3, 
    alpha: float = 0.05,
    target_power: float = 0.8
) -> Dict[str, Any]:
    """
    Perform post-hoc power analysis to verify if the achieved sample size 
    and variance are sufficient to detect the target effect size (|tau| = 0.3)
    with power >= 0.8.
    
    Logic:
    1. Separate detections and censored data.
    2. Estimate actual effect size from data variance if not provided.
    3. Calculate power using the sample size of resolved detections (since censored 
       data contributes less to correlation power).
    4. Return power estimate and sufficiency flag.
    
    Args:
        df: The full analysis dataset.
        effect_size: Target effect size (default 0.3).
        alpha: Significance level (default 0.05).
        target_power: Minimum required power (default 0.8).
    
    Returns:
        Dict with 'power_estimate', 'power_sufficient', 'n_detections', 'n_censored', 'n_total'.
    """
    verify_imports()
    
    detections, censored = quality_control_filter(df)
    n_detections = len(detections)
    n_censored = len(censored)
    n_total = len(df)
    
    logger.info(f"Power Analysis: Total={n_total}, Detections={n_detections}, Censored={n_censored}")
    
    if n_detections < 5:
        # Insufficient data for meaningful power calculation
        logger.warning("Too few detections for reliable power analysis.")
        return {
            'power_estimate': 0.0,
            'power_sufficient': False,
            'n_detections': n_detections,
            'n_censored': n_censored,
            'n_total': n_total,
            'note': 'Insufficient detections (< 5) for power calculation.'
        }
    
    # Use the provided effect_size (0.3) as the target for correlation detection
    # We approximate the power for a correlation test using a t-test approximation
    # Power = 1 - beta. We need to find beta given n, alpha, and effect_size.
    
    power_estimate = 0.0
    
    if HAS_STATSMODELS:
        # Use statsmodels for more accurate power calculation
        # TTestIndPower is for two-sample means, but we can approximate correlation power
        # by treating the effect size as Cohen's d derived from the correlation.
        # r = 0.3 -> d approx 0.64 (for equal groups).
        # However, a direct correlation power test is better.
        # Since statsmodels doesn't have a direct 'power for Kendall's tau', 
        # we use the correlation power test (Fisher's z) approximation.
        
        # Approximation: Convert tau to Pearson r (r ~ tau * 1.5 is a rough heuristic for small tau)
        # Or simply use the effect_size as a proxy for Cohen's d in a t-test context
        # which is a conservative estimate for correlation power.
        
        power_analysis = TTestIndPower()
        # We assume a two-sample scenario (High Temp vs Low Temp) with effect_size
        # This is a standard way to estimate power for correlation-like effects in regression
        power_estimate = power_analysis.solve_power(
            effect_size=effect_size, 
            nobs1=n_detections, 
            alpha=alpha, 
            power=None, 
            ratio=1.0
        )
        
        # Clamp to [0, 1]
        power_estimate = max(0.0, min(1.0, power_estimate))
        
    elif HAS_SCIPY:
        # Fallback: Use a simplified approximation based on sample size and effect size
        # Power ~ 1 - norm.cdf(z_alpha - delta)
        # delta = effect_size * sqrt(n/2) for two-sample
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2) # two-tailed
        delta = effect_size * np.sqrt(n_detections / 2)
        power_estimate = 1 - norm.cdf(z_alpha - delta)
        power_estimate = max(0.0, min(1.0, power_estimate))
    
    power_sufficient = power_estimate >= target_power
    
    return {
        'power_estimate': float(power_estimate),
        'power_sufficient': bool(power_sufficient),
        'n_detections': n_detections,
        'n_censored': n_censored,
        'n_total': n_total,
        'effect_size_target': effect_size,
        'alpha': alpha,
        'target_power': target_power
    }

def generate_quality_report(
    power_results: Dict[str, Any], 
    output_path: Path
) -> None:
    """
    Generate a human-readable markdown report summarizing the power analysis.
    
    Args:
        power_results: Dictionary returned by calculate_statistical_power.
        output_path: Path to save the markdown report.
    """
    report_lines = [
        "# Statistical Power Analysis Report",
        "",
        "## Overview",
        f"This report evaluates the statistical power of the current sample to detect",
        f"a correlation effect size (|tau|) of {power_results['effect_size_target']}.",
        "",
        "## Sample Composition",
        f"- **Total Planets**: {power_results['n_total']}",
        f"- **Resolved Detections**: {power_results['n_detections']}",
        f"- **Censored (Upper Limits)**: {power_results['n_censored']}",
        "",
        "## Power Analysis Results",
        f"- **Estimated Power**: {power_results['power_estimate']:.4f}",
        f"- **Target Power**: {power_results['target_power']}",
        f"- **Sufficient Power**: {'Yes' if power_results['power_sufficient'] else 'No'}",
        "",
    ]
    
    if 'note' in power_results:
        report_lines.append(f"**Note**: {power_results['note']}")
        report_lines.append("")
    
    if power_results['power_sufficient']:
        report_lines.append("## Conclusion")
        report_lines.append("The current sample size and variance are sufficient to detect the target effect")
        report_lines.append("size with the specified power. The study meets the evidentiary standard (SC-004).")
    else:
        report_lines.append("## Conclusion")
        report_lines.append("The current sample size is **insufficient** to guarantee detection of the target")
        report_lines.append("effect size with the specified power. The study may be underpowered.")
        report_lines.append("")
        report_lines.append("### Recommendations")
        if power_results['n_detections'] < 30:
            report_lines.append("- Increase the number of resolved detections (e.g., lower SNR threshold if physically justified, or acquire more data).")
        else:
            report_lines.append("- The effect size in the population may be smaller than the target (0.3). Consider a more conservative target.")
    
    report_content = "\n".join(report_lines)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Quality report saved to {output_path}")

def save_power_results(power_results: Dict[str, Any], output_path: Path) -> None:
    """Save power analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(power_results, f, indent=2)
    logger.info(f"Power results saved to {output_path}")

def main():
    """
    Main entry point for the power analysis task.
    Expects input dataset from previous analysis steps.
    """
    config = get_config()
    setup_logging()
    
    # Paths
    input_path = Path(config.get('analysis_dataset_path', 'data/processed/analysis_dataset.csv'))
    power_output_path = Path(config.get('power_analysis_output', 'results/power_analysis.json'))
    quality_report_path = Path(config.get('quality_report_output', 'results/quality_report.md'))
    
    logger.info(f"Starting power analysis with input: {input_path}")
    
    try:
        df = load_analysis_data(input_path)
        
        # Calculate power
        power_results = calculate_statistical_power(df, effect_size=0.3)
        
        # Save results
        save_power_results(power_results, power_output_path)
        generate_quality_report(power_results, quality_report_path)
        
        logger.info("Power analysis completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())