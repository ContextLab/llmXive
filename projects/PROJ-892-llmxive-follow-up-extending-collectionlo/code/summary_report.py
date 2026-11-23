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
    """
    Load the statistical analysis results from the JSON file.
    
    Args:
        results_path: Path to the analysis results JSON file.
        
    Returns:
        Dictionary containing the analysis results.
        
    Raises:
        FileNotFoundError: If the results file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Analysis results file not found: {results_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def format_credible_interval(estimate: float, lower: float, upper: float) -> str:
    """
    Format a credible interval as a human-readable string.
    
    Args:
        estimate: The posterior mean or median estimate.
        lower: The lower bound of the credible interval.
        upper: The upper bound of the credible interval.
        
    Returns:
        Formatted string like "0.45 [0.32, 0.58] (95% CI)"
    """
    return f"{estimate:.3f} [{lower:.3f}, {upper:.3f}] (95% CI)"

def generate_summary_report(results: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary report of the statistical findings.
    
    Args:
        results: Dictionary containing the statistical analysis results.
        
    Returns:
        Formatted summary report string.
    """
    lines = []
    lines.append("=" * 80)
    lines.append("QUANTIZATION ROBUSTNESS OF MULTI-EFFECT LoRA ADAPTERS")
    lines.append("Statistical Analysis Summary Report")
    lines.append("=" * 80)
    lines.append("")

    # Extract key metrics
    correlation_stats = results.get('correlation_stats', {})
    bayesian_results = results.get('bayesian_results', {})
    underpowered_flag = results.get('underpowered', False)

    # Section 1: Subspace Rank vs Concept Bleeding Correlation
    lines.append("1. SUBSPACE RANK VS CONCEPT BLEEDING CORRELATION")
    lines.append("-" * 40)
    
    if correlation_stats:
        correlation_coef = correlation_stats.get('correlation_coefficient', 0.0)
        ci_lower = correlation_stats.get('credible_interval_lower', 0.0)
        ci_upper = correlation_stats.get('credible_interval_upper', 0.0)
        p_value = correlation_stats.get('p_value', 'N/A')
        
        lines.append(f"   Correlation Coefficient: {format_credible_interval(correlation_coef, ci_lower, ci_upper)}")
        lines.append(f"   Statistical Significance (Bayesian): {p_value}")
        
        # Interpret the correlation
        if abs(correlation_coef) > 0.5:
            direction = "strong"
        elif abs(correlation_coef) > 0.3:
            direction = "moderate"
        else:
            direction = "weak"
        
        if correlation_coef > 0:
            relationship = "positive"
        elif correlation_coef < 0:
            relationship = "negative"
        else:
            relationship = "no"
        
        lines.append(f"   Interpretation: There is a {direction} {relationship} relationship")
        lines.append(f"   between LoRA subspace rank and concept bleeding magnitude.")
    else:
        lines.append("   No correlation statistics available.")
    
    lines.append("")

    # Section 2: Bayesian Hierarchical Model Results
    lines.append("2. BAYESIAN HIERARCHICAL MODEL RESULTS")
    lines.append("-" * 40)
    
    if bayesian_results:
        quantization_effect = bayesian_results.get('quantization_effect', {})
        posterior_mean = quantization_effect.get('posterior_mean', 0.0)
        ci_lower = quantization_effect.get('credible_interval_lower', 0.0)
        ci_upper = quantization_effect.get('credible_interval_upper', 0.0)
        
        lines.append(f"   Quantization Effect (Delta in Concept Adherence):")
        lines.append(f"   {format_credible_interval(posterior_mean, ci_lower, ci_upper)}")
        
        # Determine if the effect is significant
        if ci_lower > 0 or ci_upper < 0:
            lines.append("   Status: STATISTICALLY SIGNIFICANT (95% CI does not include 0)")
        else:
            lines.append("   Status: NOT STATISTICALLY SIGNIFICANT (95% CI includes 0)")
        
        # Additional model diagnostics
        r_squared = bayesian_results.get('r_squared', 'N/A')
        if r_squared != 'N/A':
            lines.append(f"   Model R-squared: {r_squared:.3f}")
    else:
        lines.append("   No Bayesian model results available.")
    
    lines.append("")

    # Section 3: Power Analysis
    lines.append("3. POWER ANALYSIS")
    lines.append("-" * 40)
    
    if underpowered_flag:
        lines.append("   WARNING: Results are flagged as 'Underpowered'.")
        lines.append("   The posterior width exceeds the threshold (0.2),")
        lines.append("   suggesting that more data may be needed for conclusive results.")
    else:
        lines.append("   Analysis appears adequately powered.")
    
    lines.append("")

    # Section 4: Key Findings
    lines.append("4. KEY FINDINGS")
    lines.append("-" * 40)
    
    findings = []
    
    if correlation_stats and abs(correlation_coef) > 0.3:
        if correlation_coef > 0:
            findings.append("Higher subspace ranks are associated with increased concept bleeding.")
        else:
            findings.append("Lower subspace ranks are associated with increased concept bleeding.")
    
    if bayesian_results:
        if ci_lower > 0:
            findings.append("Quantization significantly degrades concept adherence.")
        elif ci_upper < 0:
            findings.append("Quantization significantly improves concept adherence (unexpected).")
        else:
            findings.append("Quantization has no statistically significant effect on concept adherence.")
    
    if not findings:
        findings.append("No strong statistical findings detected in the current analysis.")
    
    for i, finding in enumerate(findings, 1):
        lines.append(f"   {i}. {finding}")
    
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    
    return "\n".join(lines)

def main():
    """
    Main entry point for generating the summary report.
    
    Loads the analysis results, generates a human-readable summary,
    and prints it to the console. Optionally saves to a file.
    """
    # Default paths
    project_root = Path(__file__).parent.parent
    results_path = project_root / "data" / "analysis_results.json"
    output_path = project_root / "data" / "summary_report.txt"
    
    # Allow override via command line
    if len(sys.argv) > 1:
        results_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    
    try:
        logger.info(f"Loading analysis results from: {results_path}")
        results = load_analysis_results(str(results_path))
        
        logger.info("Generating summary report...")
        report = generate_summary_report(results)
        
        # Print to console
        print(report)
        
        # Save to file
        logger.info(f"Saving report to: {output_path}")
        with open(output_path, 'w') as f:
            f.write(report)
        
        logger.info("Summary report generated successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in results file: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()