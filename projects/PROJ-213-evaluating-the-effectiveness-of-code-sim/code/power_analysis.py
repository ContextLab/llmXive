"""
Power and Sample Size Analysis for Code Simplification Evaluation.

This module implements the power analysis required by FR-010.
It calculates the minimum detectable effect (MDE) for the HumanEval dataset
(n=164) given a power of 0.8 and documents the constraint mismatch with
the specification requirement of n>=200.
"""
import math
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

# Constants
HUMAN_EVAL_SIZE = 164
SPEC_REQUIRED_SIZE = 200
POWER_TARGET = 0.80
ALPHA = 0.05
TWO_TAILED = True

# Z-scores for standard normal distribution
# Z_alpha/2 for two-tailed test at alpha=0.05 is approx 1.96
# Z_beta for power=0.80 (beta=0.20) is approx 0.84
Z_ALPHA = 1.959963984540054  # norm.ppf(1 - 0.05/2)
Z_BETA = 0.8416212335729143  # norm.ppf(0.80)

def calculate_minimum_detectable_effect(n: int, power: float, alpha: float = 0.05) -> float:
    """
    Calculate the Minimum Detectable Effect (MDE) for a proportion difference
    using the normal approximation for a paired or independent test.
    
    For a binary outcome (pass/fail) with a paired design (Wilcoxon signed-rank
    approximation for proportions), the standard error is approximated.
    
    Formula: MDE = (Z_alpha + Z_beta) * sqrt(p * (1-p) * 2 / n)
    Assuming p=0.5 (conservative, maximum variance) for worst-case scenario.
    """
    # Using p=0.5 for maximum variance (conservative estimate)
    p = 0.5
    
    # Standard error of the difference (assuming paired or similar variance)
    # For a difference in proportions: SE = sqrt( p(1-p)/n1 + p(1-p)/n2 )
    # For paired or single sample difference from baseline: SE ~ sqrt(2 * p(1-p) / n)
    # Here we use the approximation for detecting a shift in a proportion
    # SE_diff = sqrt( 2 * p * (1-p) / n )
    
    se_diff = math.sqrt(2 * p * (1 - p) / n)
    
    # MDE = (Z_alpha + Z_beta) * SE
    z_alpha = 1.96 if alpha == 0.05 else 1.645 if alpha == 0.10 else 2.576
    z_beta = 0.84 if power == 0.80 else 1.28 if power == 0.90 else 0.00
    
    mde = (z_alpha + z_beta) * se_diff
    
    return mde

def generate_power_analysis_report() -> Dict[str, Any]:
    """
    Generates the power analysis report for Section 3 of research.md.
    Includes the constraint mismatch between actual n=164 and spec n>=200.
    """
    # Calculate MDE for actual dataset size
    mde_actual = calculate_minimum_detectable_effect(HUMAN_EVAL_SIZE, POWER_TARGET, ALPHA)
    
    # Calculate MDE for spec required size
    mde_spec = calculate_minimum_detectable_effect(SPEC_REQUIRED_SIZE, POWER_TARGET, ALPHA)
    
    # Constraint mismatch details
    constraint_mismatch = {
        "specification_requirement": f"n >= {SPEC_REQUIRED_SIZE} (FR-010)",
        "actual_sample_size": HUMAN_EVAL_SIZE,
        "difference": SPEC_REQUIRED_SIZE - HUMAN_EVAL_SIZE,
        "reason": "HumanEval dataset is a fixed benchmark of 164 problems.",
        "impact": f"Reduced statistical power or larger Minimum Detectable Effect ({mde_actual:.4f} vs {mde_spec:.4f}).",
        "mitigation": "Document limitation in final report; interpret results with caution regarding small effect sizes."
    }
    
    report = {
        "section_title": "Power Analysis and Sample Size Justification",
        "dataset_name": "HumanEval",
        "sample_size": HUMAN_EVAL_SIZE,
        "target_power": POWER_TARGET,
        "significance_level": ALPHA,
        "statistical_test": "Wilcoxon Signed-Rank Test (paired)",
        "minimum_detectable_effect": {
            "value": mde_actual,
            "unit": "proportion difference (absolute)",
            "interpretation": f"With n={HUMAN_EVAL_SIZE}, the study has 80% power to detect an effect size of at least {mde_actual:.2%}."
        },
        "specification_mismatch": {
            "required_n": SPEC_REQUIRED_SIZE,
            "actual_n": HUMAN_EVAL_SIZE,
            "mismatch": True,
            "details": constraint_mismatch
        },
        "recommendations": [
            f"Accept n=164 as the maximum available sample size for HumanEval.",
            f"Acknowledge that effects smaller than {mde_actual:.2%} may not be statistically significant.",
            "Consider combining with other benchmarks if available to increase power."
        ]
    }
    
    return report

def write_research_section3(report: Dict[str, Any]) -> str:
    """
    Formats the power analysis report into Markdown for research.md Section 3.
    """
    lines = [
        "### Section 3: Power Analysis and Sample Size Justification",
        "",
        f"**Dataset**: {report['dataset_name']} (n={report['sample_size']})",
        f"**Target Power**: {report['target_power']:.0%}",
        f"**Significance Level (alpha)**: {report['significance_level']:.2f}",
        f"**Statistical Test**: {report['statistical_test']}",
        "",
        "**Minimum Detectable Effect (MDE)**:",
        f"- Value: {report['minimum_detectable_effect']['value']:.4f} ({report['minimum_detectable_effect']['value']:.2%})",
        f"- Interpretation: {report['minimum_detectable_effect']['interpretation']}",
        "",
        "**Constraint Mismatch (FR-010)**:",
        f"- Specification requires: n >= {report['specification_mismatch']['required_n']}",
        f"- Actual sample size: {report['specification_mismatch']['actual_n']}",
        f"- Mismatch: {'Yes' if report['specification_mismatch']['mismatch'] else 'No'}",
        "",
        "Details:",
        f"- Reason: {report['specification_mismatch']['details']['reason']}",
        f"- Impact: {report['specification_mismatch']['details']['impact']}",
        f"- Mitigation: {report['specification_mismatch']['details']['mitigation']}",
        "",
        "**Recommendations**:",
    ]
    
    for rec in report['recommendations']:
        lines.append(f"- {rec}")
        
    lines.append("")
    return "\n".join(lines)

def main():
    """
    Main entry point to generate the power analysis and update research.md.
    """
    # Ensure output directories exist
    research_path = Path("specs/001-eval-code-simplification/research.md")
    if not research_path.parent.exists():
        research_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate report
    report = generate_power_analysis_report()
    
    # Format section
    section_markdown = write_research_section3(report)
    
    # Read existing research.md if it exists, to preserve other sections
    if research_path.exists():
        content = research_path.read_text()
        # Simple strategy: replace or append Section 3
        # If Section 3 exists, replace it. Otherwise append.
        if "### Section 3:" in content:
            # Find start of Section 3 and end of Section 3 (start of Section 4 or EOF)
            start_idx = content.find("### Section 3:")
            next_section_idx = content.find("### Section 4:", start_idx)
            if next_section_idx == -1:
                # Section 3 is the last section
                content = content[:start_idx] + section_markdown
            else:
                content = content[:start_idx] + section_markdown + content[next_section_idx:]
        else:
            # Append if not found
            content += "\n" + section_markdown
        research_path.write_text(content)
    else:
        # Create new file with just this section for now (other sections added by other tasks)
        header = """# Research Documentation: Evaluating Code Simplification Effectiveness

"""
        research_path.write_text(header + section_markdown)
    
    print(f"Power analysis completed. Updated {research_path}")
    print(f"MDE for n={HUMAN_EVAL_SIZE}: {report['minimum_detectable_effect']['value']:.4f}")
    print(f"Constraint Mismatch: {report['specification_mismatch']['mismatch']} (Spec requires {SPEC_REQUIRED_SIZE}, Actual {HUMAN_EVAL_SIZE})")

if __name__ == "__main__":
    main()