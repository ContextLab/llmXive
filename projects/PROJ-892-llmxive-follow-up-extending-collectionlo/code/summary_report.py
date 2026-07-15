import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_analysis_results(results_path: str) -> Dict[str, Any]:
    """Load the analysis results from the JSON file."""
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Analysis results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def format_credible_interval(estimates: Dict[str, Any], param_name: str) -> str:
    """Format a parameter's posterior mean and 95% CI."""
    if param_name not in estimates:
        return f"{param_name}: Not available"
    
    param_data = estimates[param_name]
    mean = param_data.get('mean', 'N/A')
    ci_lower = param_data.get('ci_95_lower', 'N/A')
    ci_upper = param_data.get('ci_95_upper', 'N/A')
    width = param_data.get('ci_width', 'N/A')
    
    return (f"{param_name}: mean={mean:.4f}, "
            f"95% CI=[{ci_lower:.4f}, {ci_upper:.4f}], "
            f"width={width:.4f}")

def generate_summary_report(analysis_results: Dict[str, Any]) -> str:
    """Generate a human-readable summary report of the statistical findings."""
    lines = []
    lines.append("=" * 80)
    lines.append("QUANTIZATION ROBUSTNESS: STATISTICAL FINDINGS SUMMARY")
    lines.append("=" * 80)
    lines.append("")

    # 1. Model Convergence & Power Check
    model_status = analysis_results.get('model_status', {})
    convergence = model_status.get('converged', False)
    effective_samples = model_status.get('effective_samples', 0)
    r_hat_max = model_status.get('r_hat_max', float('inf'))
    
    lines.append("1. MODEL CONVERGENCE & POWER")
    lines.append("-" * 40)
    lines.append(f"   Status: {'CONVERGED' if convergence else 'NOT CONVERGED'}")
    lines.append(f"   Max R-hat: {r_hat_max:.4f} (Target < 1.05)")
    lines.append(f"   Effective Samples: {effective_samples}")
    
    power_check = model_status.get('power_check', {})
    is_underpowered = power_check.get('underpowered', False)
    width_threshold = power_check.get('threshold', 0.2)
    
    if is_underpowered:
        lines.append(f"   ⚠ WARNING: Analysis is UNDERPOWERED (CI width > {width_threshold})")
        lines.append(f"   Interpretation: Results should be treated as preliminary.")
    else:
        lines.append(f"   ✓ Analysis has sufficient power (CI width ≤ {width_threshold})")
    lines.append("")

    # 2. Quantization Effect Analysis
    lines.append("2. QUANTIZATION IMPACT ON CONCEPT ADHERENCE")
    lines.append("-" * 40)
    estimates = analysis_results.get('parameter_estimates', {})
    
    # FP16 Baseline (Intercept)
    lines.append("   Baseline (FP16) Adherence:")
    if 'intercept' in estimates:
        lines.append(f"   {format_credible_interval(estimates, 'intercept')}")
    else:
        lines.append("   (Not computed)")
    lines.append("")

    # Quantization Effects
    quant_effects = estimates.get('quantization_effects', {})
    if quant_effects:
        for effect_name, data in quant_effects.items():
            mean = data.get('mean', 'N/A')
            ci_lower = data.get('ci_95_lower', 'N/A')
            ci_upper = data.get('ci_95_upper', 'N/A')
            width = data.get('ci_width', 'N/A')
            
            # Determine significance based on CI crossing zero
            crosses_zero = (ci_lower < 0 and ci_upper > 0) if isinstance(ci_lower, float) else True
            significance = "NOT SIGNIFICANT" if crosses_zero else "SIGNIFICANT"
            direction = "DECREASE" if mean < 0 else "INCREASE" if mean > 0 else "NEUTRAL"
            
            lines.append(f"   {effect_name.upper()} Effect:")
            lines.append(f"      Mean Change: {mean:.4f}")
            lines.append(f"      95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
            lines.append(f"      Significance: {significance}")
            lines.append(f"      Direction: {direction} in adherence")
            lines.append("")
    else:
        lines.append("   (No quantization effects computed)")
    lines.append("")

    # 3. Subspace Rank Correlation
    lines.append("3. SUBSPACE RANK VS. CONCEPT BLEEDING CORRELATION")
    lines.append("-" * 40)
    correlation_data = analysis_results.get('correlation_analysis', {})
    
    if correlation_data:
        corr_mean = correlation_data.get('correlation_mean', 'N/A')
        corr_ci_lower = correlation_data.get('correlation_ci_95_lower', 'N/A')
        corr_ci_upper = correlation_data.get('correlation_ci_95_upper', 'N/A')
        
        lines.append(f"   Correlation (Rank vs. Bleeding): {corr_mean:.4f}")
        lines.append(f"   95% Credible Interval: [{corr_ci_lower:.4f}, {corr_ci_upper:.4f}]")
        
        # Interpretation
        crosses_zero = (corr_ci_lower < 0 and corr_ci_upper > 0) if isinstance(corr_ci_lower, float) else True
        if not crosses_zero:
            if corr_mean > 0:
                lines.append("   Interpretation: Higher subspace rank is associated with MORE concept bleeding.")
            else:
                lines.append("   Interpretation: Higher subspace rank is associated with LESS concept bleeding (more robust).")
        else:
            lines.append("   Interpretation: No strong evidence of a relationship between subspace rank and concept bleeding.")
    else:
        lines.append("   (Correlation analysis not available)")
    lines.append("")

    # 4. Final Conclusions
    lines.append("4. FINAL CONCLUSIONS")
    lines.append("-" * 40)
    conclusions = analysis_results.get('conclusions', [])
    if conclusions:
        for i, conclusion in enumerate(conclusions, 1):
            lines.append(f"   {i}. {conclusion}")
    else:
        # Generate generic conclusions based on data if not explicitly provided
        if quant_effects:
            lines.append("   1. Quantization effects were measured for all adapters.")
            if is_underpowered:
                lines.append("   2. Sample size may be insufficient for definitive claims.")
            else:
                lines.append("   2. Statistical power was sufficient for inference.")
        else:
            lines.append("   1. No quantization effects were detected.")
    lines.append("")
    lines.append("=" * 80)

    return "\n".join(lines)

def main():
    """Main entry point to generate the summary report."""
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    results_file = project_root / "data" / "analysis_results.json"
    output_file = project_root / "data" / "summary_report.txt"

    logger.info(f"Loading analysis results from: {results_file}")
    
    try:
        analysis_results = load_analysis_results(str(results_file))
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error("Please ensure that T027 (run_statistical_analysis) has completed successfully.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in analysis results: {e}")
        sys.exit(1)

    logger.info("Generating summary report...")
    report_text = generate_summary_report(analysis_results)

    # Print to console
    print(report_text)

    # Save to file
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    logger.info(f"Summary report saved to: {output_file}")

if __name__ == "__main__":
    main()