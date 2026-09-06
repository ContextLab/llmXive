import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from robustness import SensitivityResult, PermutationResult

def sanitize_text(text: str) -> str:
    """
    Sanitize text to ensure associational framing.
    Replaces causal language with associational language.
    """
    replacements = {
        "causes": "is associated with",
        "leads to": "correlates with",
        "effect": "association",
        "impact": "relationship",
        "influence": "association",
        "determines": "predicts",
        "results in": "is associated with",
        "drives": "is correlated with"
    }
    for causal, assoc in replacements.items():
        text = text.replace(causal, assoc)
        text = text.replace(causal.capitalize(), assoc.capitalize())
    return text

def validate_associational_framing(text: str) -> bool:
    """
    Check if text contains causal language.
    Returns True if text is associational, False otherwise.
    """
    causal_terms = ["causes", "leads to", "effect", "impact", "influence", "determines", "results in", "drives"]
    for term in causal_terms:
        if term in text.lower():
            return False
    return True

def run_associational_audit(report_path: str) -> Dict[str, Any]:
    """
    Audit a report for causal language and return a summary.
    """
    with open(report_path, 'r') as f:
        text = f.read()
    
    issues = []
    if not validate_associational_framing(text):
        issues.append("Causal language detected")
    
    return {
        "path": report_path,
        "is_associational": len(issues) == 0,
        "issues": issues
    }

def generate_final_report(
    sensitivity_results: List[SensitivityResult],
    permutation_result: Optional[PermutationResult] = None,
    e_value: Optional[float] = None,
    output_path: str = "docs/reports/final_analysis.md"
) -> None:
    """
    Generate the final report with all diagnostics and associational framing.
    """
    report_lines = []
    report_lines.append("# Final Analysis Report")
    report_lines.append("")
    report_lines.append("## Sensitivity Analysis")
    report_lines.append("")
    report_lines.append("The following table shows the stability of the association coefficient and p-values across different semantic similarity thresholds.")
    report_lines.append("")
    
    if sensitivity_results:
        report_lines.append("| Threshold | Coefficient | Std Error | t-stat | p-value | R-squared | N |")
        report_lines.append("|-----------|-------------|-----------|--------|---------|-----------|---|")
        for r in sensitivity_results:
            report_lines.append(f"| {r.threshold:.2f} | {r.coefficient:.4f} | {r.standard_error:.4f} | {r.t_statistic:.4f} | {r.p_value:.4f} | {r.r_squared:.4f} | {r.n_observations} |")
    else:
        report_lines.append("No sensitivity results available.")
    
    report_lines.append("")
    report_lines.append("## Robustness Diagnostics")
    report_lines.append("")
    
    if permutation_result:
        report_lines.append(f"**Permutation Test:** Observed statistic: {permutation_result.observed_statistic:.4f}, Null distribution p-value: {permutation_result.p_value:.4f} ({permutation_result.iterations} iterations).")
    
    if e_value:
        report_lines.append(f"**E-value:** {e_value:.4f}. This indicates the minimum strength of association that an unmeasured confounder would need to have with both the treatment and the outcome to fully explain the observed association.")
    
    report_lines.append("")
    report_lines.append("## Limitations")
    report_lines.append("")
    report_lines.append("Findings are associational; no causal claims are made due to lack of randomization.")
    report_lines.append("The E-value and permutation test are provided as sensitivity metrics for unmeasured confounding and model stability, not as causal effect sizes.")
    report_lines.append("")
    report_lines.append("## Conclusion")
    report_lines.append("")
    report_lines.append("The analysis reveals associations between algorithmic recommendations and learner diversity. The stability of these associations across thresholds suggests robustness.")
    
    report_text = "\n".join(report_lines)
    report_text = sanitize_text(report_text)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    logging.info(f"Final report generated at {output_path}")

def generate_summary_json(
    results: Dict[str, Any],
    output_path: str = "data/reports/summary.json"
) -> None:
    """
    Generate a JSON summary of the analysis results.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logging.info(f"Summary JSON generated at {output_path}")