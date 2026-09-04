"""
Uncertainty Reporting Module (Task T034).

Implements explicit Confidence Interval Reporting per Marie Curie's demand for
"quantity of data" and "uncertainty". This module reads the aggregated analysis
results, ensures 95% CIs are present for correlation and regression coefficients,
and generates a human-readable interpretation report.

Dependencies:
    - data/processed/analysis_results.json (produced by T030d/aggregate_results)
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

def load_analysis_results(input_path: Path) -> Dict[str, Any]:
    """Load the aggregated analysis results JSON."""
    if not input_path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        return json.load(f)

def ensure_confidence_intervals(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure that 95% CIs are explicitly reported for correlation and regression.
    
    If the data already contains 'ci_95' or similar, it is preserved.
    If missing, this function logs a warning (as the data should have been
    computed in previous steps) but does not fabricate values.
    
    Returns the data dictionary, potentially updated with flags indicating
    CI presence.
    """
    result = data.copy()
    
    # Check Correlation Stats
    if 'correlation' in result:
        corr = result['correlation']
        if 'ci_95' not in corr and 'ci_lower' in corr and 'ci_upper' in corr:
            # Normalize if split keys exist
            corr['ci_95'] = (corr['ci_lower'], corr['ci_upper'])
            logger.info("Normalized correlation CI from split keys.")
        elif 'ci_95' not in corr:
            logger.warning("Correlation 95% CI missing in source data.")
            corr['ci_95'] = None
        else:
            logger.info("Correlation 95% CI present.")
    
    # Check Regression Stats
    if 'regression' in result:
        reg = result['regression']
        coeffs = reg.get('coefficients', {})
        if isinstance(coeffs, dict):
            for var, val in coeffs.items():
                if isinstance(val, dict) and 'ci_95' not in val:
                    if 'ci_lower' in val and 'ci_upper' in val:
                        val['ci_95'] = (val['ci_lower'], val['ci_upper'])
                    else:
                        val['ci_95'] = None
            reg['coefficients'] = coeffs
    
    return result

def generate_uncertainty_summary(data: Dict[str, Any], sample_size: int) -> str:
    """
    Generate a Markdown summary interpreting the uncertainty intervals.
    
    Format:
    - Introduction regarding sample size (N).
    - Correlation coefficient with 95% CI interpretation.
    - Regression coefficients with 95% CI interpretation.
    - Conclusion on evidentiary strength.
    """
    lines = []
    lines.append("# Uncertainty Summary Report")
    lines.append("")
    lines.append(f"**Sample Size (N):** {sample_size}")
    lines.append("")
    lines.append("This report interprets the 95% Confidence Intervals (CI) derived from the analysis.")
    lines.append("The intervals reflect the precision of the estimated parameters given the observed data.")
    lines.append("")
    
    # Correlation Section
    if 'correlation' in data:
        corr = data['correlation']
        lines.append("## 1. Correlation Analysis (Water Abundance vs. Temperature)")
        lines.append("")
        tau = corr.get('tau', 'N/A')
        ci = corr.get('ci_95', None)
        
        lines.append(f"- **Kendall's Tau:** {tau}")
        if ci and isinstance(ci, (tuple, list)) and len(ci) == 2:
            lines.append(f"- **95% Confidence Interval:** [{ci[0]:.4f}, {ci[1]:.4f}]")
            if ci[0] > 0 or ci[1] < 0:
                lines.append("  - *Interpretation:* The interval does not contain zero, suggesting a statistically significant correlation at the 5% level.")
            else:
                lines.append("  - *Interpretation:* The interval contains zero, indicating that the correlation is not statistically distinguishable from zero at the 5% level.")
        else:
            lines.append("- **95% Confidence Interval:** Not available.")
            lines.append("  - *Interpretation:* Unable to assess significance without interval bounds.")
        lines.append("")
    
    # Regression Section
    if 'regression' in data:
        reg = data['regression']
        lines.append("## 2. Regression Analysis (Water Abundance Predictors)")
        lines.append("")
        coeffs = reg.get('coefficients', {})
        lines.append("| Variable | Coefficient | 95% CI | Significance Interpretation |")
        lines.append("| :--- | :--- | :--- | :--- |")
        
        for var, val in coeffs.items():
            if isinstance(val, dict):
                coef = val.get('coef', val.get('value', 'N/A'))
                ci = val.get('ci_95', None)
                ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci and isinstance(ci, (tuple, list)) and len(ci) == 2 else "N/A"
                sig = "Significant" if ci and isinstance(ci, (tuple, list)) and len(ci) == 2 and (ci[0] > 0 or ci[1] < 0) else "Not Significant"
                lines.append(f"| {var} | {coef:.4f} | {ci_str} | {sig} |")
        lines.append("")
    
    # Conclusion
    lines.append("## 3. Conclusion")
    lines.append("")
    if sample_size < 30:
        lines.append(f"Warning: The sample size (N={sample_size}) is below the recommended threshold for robust statistical inference.")
    else:
        lines.append(f"The sample size (N={sample_size}) provides a reasonable basis for statistical inference.")
    
    lines.append("The reported confidence intervals quantify the uncertainty in the estimated parameters.")
    lines.append("Narrower intervals indicate higher precision, while wider intervals suggest greater uncertainty.")
    lines.append("")
    
    return "\n".join(lines)

def save_uncertainty_summary(summary: str, output_path: Path) -> None:
    """Save the generated summary to a Markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(summary)
    logger.info(f"Uncertainty summary saved to {output_path}")

def main():
    config = get_config()
    input_path = Path(config['paths']['processed_data']) / 'analysis_results.json'
    output_path = Path(config['paths']['results']) / 'uncertainty_summary.md'
    
    try:
        logger.info(f"Loading analysis results from {input_path}")
        data = load_analysis_results(input_path)
        
        # Extract sample size if available, otherwise estimate or default
        sample_size = data.get('sample_size', data.get('n', 0))
        
        logger.info("Ensuring confidence intervals are present...")
        data = ensure_confidence_intervals(data)
        
        logger.info("Generating uncertainty summary...")
        summary = generate_uncertainty_summary(data, sample_size)
        
        logger.info(f"Saving summary to {output_path}")
        save_uncertainty_summary(summary, output_path)
        
        print(f"SUCCESS: Uncertainty summary generated at {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating uncertainty summary: {e}")
        raise

if __name__ == "__main__":
    main()