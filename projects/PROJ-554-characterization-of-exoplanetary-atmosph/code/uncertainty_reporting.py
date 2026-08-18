"""
T034: Review Response - Confidence Interval Reporting and Uncertainty Summary.

Implements explicit "Confidence Interval Reporting" per Marie Curie's demand for
"quantity of data" and "uncertainty".

Logic:
1. Load `data/processed/analysis_results.json` (produced by T030d).
2. Ensure it explicitly reports the 95% CI for the correlation coefficient and
   regression coefficients.
3. Generate `results/uncertainty_summary.md` interpreting these intervals in the
   context of the sample size (N).

Deliverable: `results/uncertainty_summary.md`
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import get_config
from utils import setup_logging

# Configure logging
logger = logging.getLogger(__name__)

def load_analysis_results(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load the aggregated analysis results from the JSON file."""
    results_path = Path(config["data"]["processed"]) / "analysis_results.json"
    if not results_path.exists():
        logger.error(f"Analysis results file not found: {results_path}")
        return None
    
    with open(results_path, "r") as f:
        return json.load(f)

def ensure_confidence_intervals(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure the results dictionary explicitly contains 95% CIs for correlation
    and regression coefficients. If missing, log a warning (though they should
    be present from T025c and T027).
    """
    # Check correlation CI
    if "correlation" in results:
        corr_data = results["correlation"]
        if "ci_lower" not in corr_data or "ci_upper" not in corr_data:
            logger.warning("Correlation 95% CI missing in analysis_results.json")
            # Placeholder if missing, though T025c should have generated it
            corr_data["ci_lower"] = None
            corr_data["ci_upper"] = None
        else:
            logger.info(f"Correlation 95% CI found: [{corr_data['ci_lower']:.4f}, {corr_data['ci_upper']:.4f}]")
    
    # Check regression CIs
    if "regression" in results:
        reg_data = results["regression"]
        if "coefficients" in reg_data and "confidence_intervals" not in reg_data:
            logger.warning("Regression 95% CIs missing in analysis_results.json")
            reg_data["confidence_intervals"] = {}
        else:
            logger.info("Regression 95% CIs found.")
    
    return results

def generate_uncertainty_summary(results: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    Generate the markdown content for the uncertainty summary.
    Interprets CIs in the context of sample size N.
    """
    lines = []
    lines.append("# Uncertainty Summary Report")
    lines.append("")
    lines.append("## Overview")
    lines.append("This report interprets the statistical uncertainty of the exoplanetary atmosphere analysis,")
    lines.append("focusing on the 95% Confidence Intervals (CI) for correlation and regression coefficients,")
    lines.append("as requested by reviewer Marie Curie regarding the 'quantity of data' and 'uncertainty'.")
    lines.append("")

    # Sample Size Context
    n = results.get("sample_size", 0)
    lines.append(f"### Sample Size Context")
    lines.append(f"**Total Observations (N):** {n}")
    if n < 30:
        lines.append(f"*Note: The sample size ({n}) is below the ideal target of 30. Confidence intervals may be wider and less precise.*")
    elif n > 45:
        lines.append(f"*Note: The sample size ({n}) exceeds the target range of 30-45, providing robust statistical power.*")
    else:
        lines.append(f"*The sample size falls within the target range (30-45), balancing feasibility and statistical power.*")
    lines.append("")

    # Correlation Uncertainty
    lines.append("## Correlation Analysis Uncertainty")
    lines.append("")
    if "correlation" in results:
        corr = results["correlation"]
        tau = corr.get("kendall_tau", "N/A")
        p_val = corr.get("p_value", "N/A")
        ci_lower = corr.get("ci_lower")
        ci_upper = corr.get("ci_upper")
        
        lines.append(f"- **Kendall's Tau:** {tau}")
        lines.append(f"- **P-value:** {p_val}")
        
        if ci_lower is not None and ci_upper is not None:
            ci_width = ci_upper - ci_lower
            lines.append(f"- **95% Confidence Interval:** [{ci_lower:.4f}, {ci_upper:.4f}]")
            lines.append(f"- **CI Width:** {ci_width:.4f}")
            lines.append("")
            lines.append("**Interpretation:**")
            if ci_width <= 0.2:
                lines.append("The confidence interval width is narrow (<= 0.2 dex), indicating a robust estimate of the correlation coefficient.")
            else:
                lines.append("The confidence interval width is wide (> 0.2 dex), suggesting higher uncertainty in the correlation estimate.")
            lines.append("This interval quantifies the range within which the true correlation likely lies, given the observed data.")
        else:
            lines.append("- **95% Confidence Interval:** Not available.")
            lines.append("**Interpretation:** Unable to assess uncertainty bounds for correlation.")
    else:
        lines.append("*Correlation analysis results not found.*")
    lines.append("")

    # Regression Uncertainty
    lines.append("## Regression Analysis Uncertainty")
    lines.append("")
    if "regression" in results:
        reg = results["regression"]
        coeffs = reg.get("coefficients", {})
        cis = reg.get("confidence_intervals", {})
        fallback = reg.get("fallback_triggered", False)
        
        if fallback:
            lines.append("**Model Type:** Survival Regression (Cox/AFT) - Fallback triggered due to multicollinearity (VIF > 5).")
        else:
            lines.append("**Model Type:** Tobit Regression (Censored Data).")
        
        lines.append("")
        lines.append("| Predictor | Coefficient | 95% CI Lower | 95% CI Upper | Interpretation |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        
        for var, coef in coeffs.items():
            ci_low = cis.get(var, {}).get("lower", "N/A")
            ci_high = cis.get(var, {}).get("upper", "N/A")
            
            # Simple interpretation logic
            if ci_low == "N/A" or ci_high == "N/A":
                interp = "Uncertainty not computed"
            else:
                try:
                    low_f = float(ci_low)
                    high_f = float(ci_high)
                    if low_f > 0 and high_f > 0:
                        interp = "Positive association"
                    elif low_f < 0 and high_f < 0:
                        interp = "Negative association"
                    else:
                        interp = "Inconclusive (CI includes 0)"
                except ValueError:
                    interp = "Invalid CI values"
            
            lines.append(f"| {var} | {coef:.4f} | {ci_low} | {ci_high} | {interp} |")
        
        lines.append("")
        lines.append("**Interpretation:**")
        lines.append("The regression coefficients represent the estimated change in water abundance per unit change in the predictor.")
        lines.append("The 95% Confidence Intervals indicate the precision of these estimates. If an interval includes 0, the predictor")
        lines.append("may not have a statistically significant effect at the 5% level.")
    else:
        lines.append("*Regression analysis results not found.*")
    lines.append("")

    # Conclusion
    lines.append("## Conclusion")
    lines.append("")
    lines.append("This report explicitly documents the uncertainty associated with the derived correlations and regression coefficients.")
    lines.append("By providing the 95% Confidence Intervals, we adhere to the scientific standard of reporting not just the point estimate")
    lines.append("but the range of plausible values, ensuring the 'quantity of data' is contextualized by its 'uncertainty'.")
    lines.append("")
    lines.append("---")
    lines.append("*Generated by T034: Uncertainty Reporting Module*")

    return "\n".join(lines)

def save_uncertainty_summary(content: str, config: Dict[str, Any]) -> Path:
    """Save the generated markdown to the results directory."""
    results_dir = Path(config["results"])
    results_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = results_dir / "uncertainty_summary.md"
    with open(output_path, "w") as f:
        f.write(content)
    
    logger.info(f"Uncertainty summary saved to: {output_path}")
    return output_path

def main():
    """Main entry point for T034."""
    config = get_config()
    setup_logging(config)
    
    logger.info("Starting T034: Uncertainty Reporting")
    
    # 1. Load results
    results = load_analysis_results(config)
    if results is None:
        logger.error("Failed to load analysis results. Cannot proceed with T034.")
        return 1
    
    # 2. Ensure CIs are present
    results = ensure_confidence_intervals(results)
    
    # 3. Generate summary
    summary_content = generate_uncertainty_summary(results, config)
    
    # 4. Save summary
    output_path = save_uncertainty_summary(summary_content, config)
    
    logger.info("T034 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
