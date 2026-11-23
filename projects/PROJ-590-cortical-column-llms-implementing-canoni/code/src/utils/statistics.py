"""
Statistics utilities for gradient distribution analysis.
Implements SC-002 verification: Gradient stability and distribution comparison.
"""
import json
import os
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def load_gradient_norms(file_path: str) -> Dict[str, Any]:
    """
    Load gradient norms from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing gradient norms.
        
    Returns:
        Dictionary containing gradient norm data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Gradient norms file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return data

def extract_gradient_values(gradient_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract all gradient norm values from the loaded data structure.
    
    Args:
        gradient_data: Dictionary containing gradient norm data.
        
    Returns:
        1D numpy array of all gradient norm values.
    """
    values = []
    
    # Handle different data structures that might be returned
    if isinstance(gradient_data, dict):
        # Case 1: Data is structured as {step: {param_name: norm}}
        for step_key, step_data in gradient_data.items():
            if isinstance(step_data, dict):
                for param_name, norm in step_data.items():
                    if isinstance(norm, (int, float, np.number)):
                        values.append(float(norm))
            elif isinstance(step_data, list):
                # Case 2: Data is structured as {step: [norm1, norm2, ...]}
                for norm in step_data:
                    if isinstance(norm, (int, float, np.number)):
                        values.append(float(norm))
    elif isinstance(gradient_data, list):
        # Case 3: Data is a flat list of values or dicts with 'norm' key
        for item in gradient_data:
            if isinstance(item, (int, float, np.number)):
                values.append(float(item))
            elif isinstance(item, dict):
                if 'norm' in item:
                    values.append(float(item['norm']))
                elif 'value' in item:
                    values.append(float(item['value']))
    
    if not values:
        logger.warning("No gradient norm values found in the data structure")
        return np.array([])
    
    return np.array(values)

def verify_gradient_distribution(
    baseline_file: str,
    microcircuit_file: str,
    output_file: str
) -> Dict[str, Any]:
    """
    Verify the distribution of gradient norms by comparing baseline and microcircuit.
    Performs a two-sample Kolmogorov-Smirnov test to compare distributions.
    
    Args:
        baseline_file: Path to the baseline gradient distribution JSON file.
        microcircuit_file: Path to the microcircuit gradient distribution JSON file.
        output_file: Path to write the markdown report.
        
    Returns:
        Dictionary containing the test results and statistics.
        
    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If the data extraction fails or produces empty arrays.
    """
    # Load data
    logger.info(f"Loading baseline gradient norms from: {baseline_file}")
    baseline_data = load_gradient_norms(baseline_file)
    baseline_values = extract_gradient_values(baseline_data)
    
    logger.info(f"Loading microcircuit gradient norms from: {microcircuit_file}")
    microcircuit_data = load_gradient_norms(microcircuit_file)
    microcircuit_values = extract_gradient_values(microcircuit_data)
    
    if len(baseline_values) == 0:
        raise ValueError("Baseline gradient values array is empty")
    if len(microcircuit_values) == 0:
        raise ValueError("Microcircuit gradient values array is empty")
    
    logger.info(f"Baseline gradient norms: {len(baseline_values)} samples")
    logger.info(f"Microcircuit gradient norms: {len(microcircuit_values)} samples")
    
    # Compute descriptive statistics
    baseline_mean = np.mean(baseline_values)
    baseline_std = np.std(baseline_values)
    baseline_variance = np.var(baseline_values)
    baseline_median = np.median(baseline_values)
    
    microcircuit_mean = np.mean(microcircuit_values)
    microcircuit_std = np.std(microcircuit_values)
    microcircuit_variance = np.var(microcircuit_values)
    microcircuit_median = np.median(microcircuit_values)
    
    # Perform Kolmogorov-Smirnov test
    ks_statistic, p_value = stats.ks_2samp(baseline_values, microcircuit_values)
    
    # Compute overlap (approximate using histogram intersection)
    # Normalize histograms to compare distributions
    hist_baseline, bin_edges = np.histogram(baseline_values, bins=50, density=True)
    hist_micro, _ = np.histogram(microcircuit_values, bins=bin_edges, density=True)
    
    # Histogram intersection as a measure of overlap
    overlap = np.sum(np.minimum(hist_baseline, hist_micro)) * np.diff(bin_edges).mean()
    
    # Determine if distributions are significantly different
    alpha = 0.05
    is_significantly_different = p_value < alpha
    
    results = {
        "baseline": {
            "n_samples": len(baseline_values),
            "mean": float(baseline_mean),
            "std": float(baseline_std),
            "variance": float(baseline_variance),
            "median": float(baseline_median)
        },
        "microcircuit": {
            "n_samples": len(microcircuit_values),
            "mean": float(microcircuit_mean),
            "std": float(microcircuit_std),
            "variance": float(microcircuit_variance),
            "median": float(microcircuit_median)
        },
        "ks_test": {
            "statistic": float(ks_statistic),
            "p_value": float(p_value),
            "alpha": alpha,
            "is_significantly_different": is_significantly_different
        },
        "distribution_overlap": float(overlap),
        "interpretation": {
            "variance_ratio": float(microcircuit_variance / baseline_variance) if baseline_variance > 0 else float('inf'),
            "mean_ratio": float(microcircuit_mean / baseline_mean) if baseline_mean > 0 else float('inf')
        }
    }
    
    # Generate markdown report
    report_lines = [
        "# Gradient Distribution Verification Report (SC-002)",
        "",
        "## Overview",
        "This report verifies the distribution of gradient norms between the baseline Transformer",
        "and the Cortical Column Microcircuit model, as required by SC-002 (Gradient Stability).",
        "",
        "## Methodology",
        "A two-sample Kolmogorov-Smirnov (KS) test was performed to compare the gradient norm",
        "distributions. The null hypothesis is that both samples are drawn from the same distribution.",
        "",
        "## Descriptive Statistics",
        "",
        "### Baseline Transformer",
        f"- **Samples**: {results['baseline']['n_samples']}",
        f"- **Mean**: {results['baseline']['mean']:.6f}",
        f"- **Std Dev**: {results['baseline']['std']:.6f}",
        f"- **Variance**: {results['baseline']['variance']:.6f}",
        f"- **Median**: {results['baseline']['median']:.6f}",
        "",
        "### Microcircuit Model",
        f"- **Samples**: {results['microcircuit']['n_samples']}",
        f"- **Mean**: {results['microcircuit']['mean']:.6f}",
        f"- **Std Dev**: {results['microcircuit']['std']:.6f}",
        f"- **Variance**: {results['microcircuit']['variance']:.6f}",
        f"- **Median**: {results['microcircuit']['median']:.6f}",
        "",
        "## Kolmogorov-Smirnov Test Results",
        f"- **KS Statistic**: {results['ks_test']['statistic']:.6f}",
        f"- **P-value**: {results['ks_test']['p_value']:.6f}",
        f"- **Significance Level (α)**: {results['ks_test']['alpha']}",
        f"- **Distributions Significantly Different**: {'Yes' if results['ks_test']['is_significantly_different'] else 'No'}",
        "",
        "## Interpretation",
        "",
        f"The variance ratio (Microcircuit / Baseline) is **{results['interpretation']['variance_ratio']:.4f}**.",
        f"The mean ratio (Microcircuit / Baseline) is **{results['interpretation']['mean_ratio']:.4f}**.",
        "",
        "### Distribution Overlap",
        f"The approximate histogram intersection overlap is **{results['distribution_overlap']:.4f}**.",
        "A value of 1.0 indicates identical distributions, while 0.0 indicates no overlap.",
        "",
        "## Conclusion",
        ""
    ]
    
    if results['ks_test']['is_significantly_different']:
        report_lines.append(
            "The gradient distributions are **statistically significantly different** "
            f"(p < {alpha}). This suggests that the microcircuit architecture induces a "
            "distinct gradient flow pattern compared to the baseline Transformer."
        )
    else:
        report_lines.append(
            "The gradient distributions are **not statistically significantly different** "
            f"(p >= {alpha}). The microcircuit architecture maintains gradient stability "
            "comparable to the baseline Transformer."
        )
    
    report_lines.extend([
        "",
        "### Variance Analysis",
        ""
    ])
    
    if results['interpretation']['variance_ratio'] > 1.2:
        report_lines.append(
            "The microcircuit model exhibits **higher variance** in gradient norms, "
            "which may indicate more dynamic or unstable learning dynamics."
        )
    elif results['interpretation']['variance_ratio'] < 0.8:
        report_lines.append(
            "The microcircuit model exhibits **lower variance** in gradient norms, "
            "suggesting more stable gradient flow potentially due to homeostatic scaling."
        )
    else:
        report_lines.append(
            "The variance in gradient norms is **comparable** between the two models."
        )
    
    report_lines.extend([
        "",
        "---",
        f"*Generated by T071: Gradient Distribution Verification*",
        ""
    ])
    
    # Write report
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Report written to: {output_file}")
    
    return results

def compare_gradient_stability(
    baseline_file: str,
    microcircuit_file: str,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Wrapper function to compare gradient stability, delegating to verify_gradient_distribution.
    This maintains API compatibility with existing scripts.
    """
    if output_file is None:
        output_file = "data/logs/gradient_stability_report.md"
    return verify_gradient_distribution(baseline_file, microcircuit_file, output_file)

def main():
    """CLI entry point for gradient distribution verification."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify gradient distribution between baseline and microcircuit models."
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default="data/logs/baseline_gradient_distributions.json",
        help="Path to baseline gradient norms JSON file"
    )
    parser.add_argument(
        "--microcircuit",
        type=str,
        default="data/logs/gradient_norms.json",
        help="Path to microcircuit gradient norms JSON file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/logs/gradient_distribution_report.md",
        help="Path to output markdown report"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = verify_gradient_distribution(
            args.baseline,
            args.microcircuit,
            args.output
        )
        print(f"Verification complete. P-value: {results['ks_test']['p_value']:.6f}")
        print(f"Distributions significantly different: {results['ks_test']['is_significantly_different']}")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
