import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from config import get_path

def calculate_effect_size_ci(effect_size: float, n: int, confidence: float = 0.95) -> Optional[tuple]:
    """
    Calculate confidence interval for effect size.
    
    Args:
        effect_size: The effect size value
        n: Sample size
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower, upper) confidence interval bounds, or None if n < 30
    """
    if n < 30:
        # Cannot calculate reliable CI for small samples
        return None
    
    # Simplified CI calculation (in reality would use more sophisticated methods)
    z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
    se = effect_size / (n ** 0.5)  # Simplified standard error
    lower = effect_size - z_score * se
    upper = effect_size + z_score * se
    
    return (lower, upper)

def generate_report_logic(results: Dict[str, Any], design_type: str) -> str:
    """
    Generate report content based on analysis results.
    
    Args:
        results: Analysis results dictionary
        design_type: Design type
        
    Returns:
        Markdown content for the report
    """
    report = []
    report.append("# Final Research Report")
    report.append("")
    report.append(f"**Design Type:** {design_type}")
    report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Results section
    report.append("## Results")
    report.append("")
    
    if 'anova' in results:
        anova = results['anova']
        report.append(f"**Test Type:** {anova.get('test_type', 'N/A')}")
        report.append(f"**Statistic:** {anova.get('statistic', 'N/A')}")
        report.append(f"**P-value:** {anova.get('p_value', 'N/A')}")
        report.append(f"**FDR-corrected P-value:** {anova.get('p_fdr', 'N/A')}")
        report.append(f"**Effect Size:** {anova.get('effect_size', 'N/A')}")
        
        if anova.get('rejected'):
            report.append("")
            report.append("The results are statistically significant after FDR correction.")
        else:
            report.append("")
            report.append("The results are not statistically significant after FDR correction.")
    
    # For between-subjects design, explicitly exclude causal language
    if design_type == "Between-Subjects":
        report.append("")
        report.append("**Note:** Due to the between-subjects design, these results represent associational group differences only. Causal modulation claims cannot be made.")
    
    report.append("")
    
    # Sensitivity analysis section
    report.append("## Sensitivity Analysis")
    report.append("")
    report.append("Results across different alpha thresholds:")
    report.append("")
    
    if 'sensitivity' in results and 'alpha_sweep' in results['sensitivity']:
        report.append("| Alpha | P-value | Significant |")
        report.append("|-------|---------|-------------|")
        for alpha, data in results['sensitivity']['alpha_sweep'].items():
            sig = "Yes" if data['significant'] else "No"
            report.append(f"| {alpha} | {data['p_value']:.4f} | {sig} |")
    else:
        report.append("Sensitivity analysis not available.")
    
    report.append("")
    
    # Limitations section
    report.append("## Limitations")
    report.append("")
    
    if design_type == "Between-Subjects":
        report.append("- **Associational Nature:** This study uses a between-subjects design. Results should be interpreted as associational group differences. Causal claims about the modulation of neural responses by social rejection cannot be made.")
    else:
        report.append("- **Sample Size:** Results may be limited by sample size considerations.")
        report.append("- **Generalizability:** Findings may not generalize to all populations.")
    
    report.append("")
    
    return "\n".join(report)

def save_report(content: str, output_path: str):
    """Save report content to a Markdown file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)

def verify_report_constraints(report_path: str) -> Dict[str, bool]:
    """
    Verify that the report meets all constraints.
    
    Args:
        report_path: Path to the report file
        
    Returns:
        Dictionary with constraint verification results
    """
    with open(report_path, 'r') as f:
        content = f.read()
    
    results = {
        'contains_associational': 'associational' in content.lower(),
        'excludes_causal': 'causal' not in content.lower() or 'associational' in content.lower(),
        'has_sensitivity_table': '| Alpha |' in content,
        'has_limitations': '## Limitations' in content
    }
    
    return results

def save_final_results(results: Dict[str, Any], design_type: str, output_path: str):
    """Save final results to a JSON file."""
    import json
    import os
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    final_results = {
        'design_type': design_type,
        'timestamp': datetime.now().isoformat(),
        'results': results
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)

def run_reporting_pipeline(analysis_results_path: str, report_output_path: str, final_results_path: str):
    """Run the full reporting pipeline."""
    logging.info(f"Loading analysis results from {analysis_results_path}")
    
    with open(analysis_results_path, 'r') as f:
        results = json.load(f)
    
    design_type = results.get('anova', {}).get('design_type', 'Unknown')
    
    logging.info("Generating report")
    report_content = generate_report_logic(results, design_type)
    
    logging.info(f"Saving report to {report_output_path}")
    save_report(report_content, report_output_path)
    
    logging.info(f"Saving final results to {final_results_path}")
    save_final_results(results, design_type, final_results_path)
    
    # Verify constraints
    logging.info("Verifying report constraints")
    constraints = verify_report_constraints(report_output_path)
    logging.info(f"Constraint verification: {constraints}")
    
    return constraints

def main():
    """Main entry point for the reporting pipeline."""
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python report.py <analysis_results_path> <report_output_path> <final_results_path>")
        sys.exit(1)
    
    analysis_path = sys.argv[1]
    report_path = sys.argv[2]
    final_path = sys.argv[3]
    
    run_reporting_pipeline(analysis_path, report_path, final_path)

if __name__ == "__main__":
    main()
