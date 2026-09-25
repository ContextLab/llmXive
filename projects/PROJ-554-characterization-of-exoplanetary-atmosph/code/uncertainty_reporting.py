"""
Uncertainty Reporting Module for T034.

Implements explicit Confidence Interval Reporting per Marie Curie's demand for
"quantity of data" and "uncertainty". Generates a summary markdown report
interpreting confidence intervals in the context of the sample size.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_analysis_results(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load the aggregated analysis results from data/processed/analysis_results.json.

    Args:
        config: Optional configuration dictionary. If None, uses get_config().

    Returns:
        Dictionary containing correlation stats, regression results, and robustness reports.
    """
    if config is None:
        config = get_config()
    
    # Determine the project root based on config or default
    project_root = Path(config.get('project_root', '.'))
    results_path = project_root / 'data' / 'processed' / 'analysis_results.json'

    if not results_path.exists():
        raise FileNotFoundError(f"Analysis results file not found at {results_path}. "
                                "Ensure T030b (generate_analysis_results) has run.")

    with open(results_path, 'r') as f:
        return json.load(f)

def ensure_confidence_intervals(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure that the loaded data explicitly reports 95% CIs for correlation and regression.

    This function validates the structure required by SC-001 and SC-003:
    1. Correlation: Must have 'tau', 'p_value', and 'ci_95' (tuple or list of [lower, upper]).
    2. Regression: Coefficients must have 'ci_lower' and 'ci_upper' or a 'ci_95' structure.
    3. Water Distribution: Must have 'water_ci_width' derived from bootstrap means.

    Args:
        data: The raw analysis results dictionary.

    Returns:
        A normalized dictionary with guaranteed CI fields for reporting.
    """
    normalized = {
        'correlation': {},
        'regression': {},
        'robustness': {},
        'sample_size': data.get('sample_size', 0),
        'warnings': []
    }

    # 1. Process Correlation Stats (from T025b)
    corr_data = data.get('correlation_stats', {})
    if not corr_data:
        normalized['warnings'].append("Missing correlation_stats in analysis_results.json")
    else:
        tau = corr_data.get('tau')
        ci = corr_data.get('ci_95') or corr_data.get('confidence_interval')
        
        if tau is not None:
            normalized['correlation']['tau'] = tau
        else:
            normalized['warnings'].append("Missing 'tau' value in correlation stats")
        
        if ci and len(ci) == 2:
            normalized['correlation']['ci_lower'] = ci[0]
            normalized['correlation']['ci_upper'] = ci[1]
            normalized['correlation']['ci_width'] = ci[1] - ci[0]
        else:
            normalized['warnings'].append("Missing or malformed 'ci_95' in correlation stats")

    # 2. Process Regression Results (from T027)
    reg_data = data.get('regression_results', {})
    if not reg_data:
        normalized['warnings'].append("Missing regression_results in analysis_results.json")
    else:
        # Expecting coefficients with CIs
        coeffs = reg_data.get('coefficients', {})
        normalized['regression']['coefficients'] = coeffs
        
        # Check for overall model CI if available (e.g., from robustness check)
        robust = data.get('robustness_report', {})
        if 'ci_width_tau' in robust:
            normalized['robustness']['ci_width_tau'] = robust['ci_width_tau']
        if 'ci_width_water' in robust:
            normalized['robustness']['ci_width_water'] = robust['ci_width_water']
            # SC-003 verification
            if robust['ci_width_water'] > 0.2:
                normalized['warnings'].append(f"SC-003 Threshold Failed: Water CI width ({robust['ci_width_water']:.4f}) > 0.2")
            else:
                normalized['robustness']['sc003_met'] = True

    # 3. Process Bootstrap CI (from T025b)
    bootstrap_data = data.get('bootstrap_ci', {})
    if bootstrap_data:
        normalized['bootstrap'] = {
            'iterations': bootstrap_data.get('iterations', 0),
            'ci_lower': bootstrap_data.get('ci_lower'),
            'ci_upper': bootstrap_data.get('ci_upper'),
            'tau_mean': bootstrap_data.get('tau_mean')
        }

    return normalized

def generate_uncertainty_summary(norm_data: Dict[str, Any]) -> str:
    """
    Generate a Markdown string interpreting the confidence intervals in the context of N.

    This addresses Marie Curie's demand for "quantity of data" and "uncertainty".

    Args:
        norm_data: Normalized data from ensure_confidence_intervals.

    Returns:
        Markdown content string.
    """
    n = norm_data.get('sample_size', 0)
    corr = norm_data.get('correlation', {})
    robust = norm_data.get('robustness', {})
    warnings = norm_data.get('warnings', [])

    lines = [
        "# Uncertainty Summary Report",
        "",
        f"**Sample Size (N):** {n}",
        "",
        "## 1. Correlation Analysis (Water vs Temperature)",
        "",
    ]

    if corr:
        tau = corr.get('tau')
        ci_lower = corr.get('ci_lower')
        ci_upper = corr.get('ci_upper')
        ci_width = corr.get('ci_width')

        lines.append(f"- **Kendall's Tau:** {tau:.4f if tau is not None else 'N/A'}")
        if ci_lower is not None and ci_upper is not None:
            lines.append(f"- **95% Confidence Interval:** [{ci_lower:.4f}, {ci_upper:.4f}]")
            lines.append(f"- **CI Width:** {ci_width:.4f}")
            
            # Interpret width
            if ci_width is not None:
                if ci_width < 0.1:
                    lines.append("  - *Interpretation:* The confidence interval is narrow, indicating high precision in the correlation estimate given the sample size.")
                elif ci_width < 0.3:
                    lines.append("  - *Interpretation:* The confidence interval is moderate. While a correlation is detected, the exact magnitude has some uncertainty.")
                else:
                    lines.append("  - *Interpretation:* The confidence interval is wide. The sample size (N) may be insufficient to precisely quantify the correlation strength.")
        else:
            lines.append("- **Confidence Interval:** Not available")
    else:
        lines.append("- **Correlation Data:** Not available")

    lines.extend([
        "",
        "## 2. Robustness Checks (SC-003 Verification)",
        "",
    ])

    if robust:
        water_width = robust.get('ci_width_water')
        if water_width is not None:
            lines.append(f"- **Water Mixing Ratio CI Width:** {water_width:.4f} dex")
            if robust.get('sc003_met'):
                lines.append("  - **Status:** PASS (Width <= 0.2 dex)")
            else:
                lines.append("  - **Status:** FAIL (Width > 0.2 dex) - Precision does not meet SC-003 standard.")
        else:
            lines.append("- **Water Mixing Ratio CI Width:** Not calculated")
    else:
        lines.append("- **Robustness Data:** Not available")

    lines.extend([
        "",
        "## 3. Data Quantity and Instrumental Context",
        "",
        f"This analysis is based on **{n}** planetary spectra. ",
        "Per Marie Curie's evidentiary standards, the precision of the result is directly tied to the quantity of photons (spectral resolution) and the stability of the detector (SNR). ",
        "The confidence intervals reported above reflect the combined uncertainty from measurement noise and sample variance.",
        "",
    ])

    if warnings:
        lines.append("## 4. Warnings and Notes")
        lines.append("")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by T034: Review Response - Confidence Interval Reporting*")

    return "\n".join(lines)

def save_uncertainty_summary(content: str, output_path: Optional[str] = None) -> Path:
    """
    Save the generated markdown summary to disk.

    Args:
        content: The markdown string content.
        output_path: Optional path to save the file. Defaults to results/uncertainty_summary.md.

    Returns:
        Path to the saved file.
    """
    config = get_config()
    project_root = Path(config.get('project_root', '.'))
    
    if output_path is None:
        output_path = project_root / 'results' / 'uncertainty_summary.md'
    else:
        output_path = Path(output_path)

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(content)

    logger.info(f"Uncertainty summary saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for T034.
    1. Load analysis_results.json.
    2. Validate CI presence.
    3. Generate summary markdown.
    4. Save to results/uncertainty_summary.md.
    """
    # Setup logging if not already done
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO)

    try:
        # 1. Load Data
        logger.info("Loading analysis results...")
        raw_data = load_analysis_results()

        # 2. Normalize and Validate
        logger.info("Ensuring confidence intervals are present...")
        norm_data = ensure_confidence_intervals(raw_data)

        # 3. Generate Report
        logger.info("Generating uncertainty summary...")
        summary_md = generate_uncertainty_summary(norm_data)

        # 4. Save
        logger.info("Saving summary to disk...")
        save_uncertainty_summary(summary_md)

        logger.info("T034 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating uncertainty summary: {e}")
        raise

if __name__ == "__main__":
    main()