import math
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

def calculate_minimum_detectable_effect(n: int, power: float = 0.8, alpha: float = 0.05) -> float:
    """
    Calculate the minimum detectable effect size (Cohen's d) for a paired design
    given sample size n, target power, and significance level alpha.
    
    Uses the approximation for paired t-test power:
    d = (z_{1-alpha/2} + z_{power}) / sqrt(n)
    
    Args:
        n: Sample size (number of pairs)
        power: Target statistical power (default 0.8)
        alpha: Significance level (default 0.05)
        
    Returns:
        Minimum detectable effect size (Cohen's d)
    """
    # Critical z-values (standard normal distribution)
    # z_{1-alpha/2} for two-tailed test
    z_alpha = 1.96 if alpha == 0.05 else 2.576  # Approximation for common alphas
    
    # z_{power}
    z_power = 0.84 if power == 0.8 else 1.28  # Approximation for common powers
    
    # Effect size formula for paired design
    d = (z_alpha + z_power) / math.sqrt(n)
    return d

def generate_power_analysis_report(
    n_actual: int,
    n_required: int,
    target_power: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a comprehensive power analysis report documenting the sample size
    justification and any constraint mismatches.
    
    Args:
        n_actual: Actual sample size available (e.g., 164 for HumanEval)
        n_required: Required sample size per specification (e.g., 200)
        target_power: Target statistical power
        alpha: Significance level
        
    Returns:
        Dictionary containing power analysis results
    """
    mde_actual = calculate_minimum_detectable_effect(n_actual, target_power, alpha)
    mde_required = calculate_minimum_detectable_effect(n_required, target_power, alpha)
    
    # Calculate power mismatch
    constraint_mismatch = n_actual < n_required
    
    report = {
        "sample_size": {
            "actual": n_actual,
            "required_by_spec": n_required,
            "constraint_mismatch": constraint_mismatch,
            "mismatch_reason": f"Specification FR-010 requires n≥{n_required}, but HumanEval dataset provides n={n_actual}"
        },
        "power_analysis": {
            "target_power": target_power,
            "significance_level": alpha,
            "minimum_detectable_effect_actual": round(mde_actual, 4),
            "minimum_detectable_effect_required": round(mde_required, 4),
            "interpretation": (
                f"With n={n_actual}, the minimum detectable effect size is {mde_actual:.4f} "
                f"(Cohen's d) at {target_power*100}% power and α={alpha}. "
                f"This is larger than the {mde_required:.4f} achievable with n={n_required}."
            )
        },
        "mitigation": {
            "strategy": "document_limitation",
            "description": "Document the reduced statistical power in the final report and note that the study is underpowered to detect small effect sizes.",
            "recommendation": "Interpret non-significant results with caution; focus on effect size estimates rather than binary significance decisions."
        },
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "dataset": "HumanEval",
            "statistical_test": "Paired Wilcoxon signed-rank test (per spec FR-005)"
        }
    }
    
    return report

def write_research_section3(report: Dict[str, Any]) -> str:
    """
    Format the power analysis report as Markdown content for research.md Section 3.
    
    Args:
        report: Power analysis report dictionary
        
    Returns:
        Markdown string formatted for research.md Section 3
    """
    lines = [
        "## Section 3: Power Analysis and Sample Size Justification",
        "",
        "### FR-010 Compliance: Sample Size Requirements",
        "",
        f"- **Actual Sample Size (n)**: {report['sample_size']['actual']}",
        f"- **Required Sample Size (per FR-010)**: n ≥ {report['sample_size']['required_by_spec']}",
        f"- **Constraint Mismatch**: {report['sample_size']['constraint_mismatch']}",
        "",
        "### Constraint Mismatch Details",
        "",
        f"**Issue**: {report['sample_size']['mismatch_reason']}",
        "",
        "### Power Analysis Results",
        "",
        "| Parameter | Value |",
        "|-----------|-------|",
        f"| Target Power | {report['power_analysis']['target_power']} |",
        f"| Significance Level (α) | {report['power_analysis']['significance_level']} |",
        f"| Minimum Detectable Effect (n={report['sample_size']['actual']}) | {report['power_analysis']['minimum_detectable_effect_actual']} |",
        f"| Minimum Detectable Effect (n={report['sample_size']['required_by_spec']}) | {report['power_analysis']['minimum_detectable_effect_required']} |",
        "",
        "### Interpretation",
        "",
        report['power_analysis']['interpretation'],
        "",
        "### Mitigation Strategy",
        "",
        f"- **Strategy**: {report['mitigation']['strategy']}",
        f"- **Description**: {report['mitigation']['description']}",
        f"- **Recommendation**: {report['mitigation']['recommendation']}",
        "",
        "### Notes",
        "",
        "- This analysis assumes a paired design (Wilcoxon signed-rank test) as specified in FR-005.",
        "- The minimum detectable effect is calculated using Cohen's d approximation for paired t-tests.",
        "- For Wilcoxon tests, the rank-biserial correlation may be reported as a supplementary effect size measure.",
        "",
        f"*Generated: {report['metadata']['generated_at']}*"
    ]
    
    return "\n".join(lines)

def main():
    """
    Main entry point to generate power analysis report and write to research.md Section 3.
    """
    # Configuration from spec FR-010 and HumanEval dataset characteristics
    N_ACTUAL = 164  # HumanEval problem count
    N_REQUIRED = 200  # Per FR-010 specification
    TARGET_POWER = 0.8
    ALPHA = 0.05
    
    # Generate report
    report = generate_power_analysis_report(N_ACTUAL, N_REQUIRED, TARGET_POWER, ALPHA)
    
    # Write Section 3 content
    section3_content = write_research_section3(report)
    
    # Save to research.md (append or create)
    research_path = Path("research.md")
    
    if research_path.exists():
        # Read existing content
        content = research_path.read_text()
        # Find Section 3 position or append
        if "## Section 3:" in content:
            # Replace existing Section 3
            parts = content.split("## Section 3:")
            if len(parts) > 1:
                # Find next section start
                next_section_idx = parts[1].find("\n## Section")
                if next_section_idx != -1:
                    new_content = parts[0] + "## Section 3:" + section3_content + "\n\n" + parts[1][next_section_idx:]
                else:
                    new_content = parts[0] + "## Section 3:" + section3_content
            else:
                new_content = content + "\n\n## Section 3:" + section3_content
        else:
            new_content = content + "\n\n" + section3_content
    else:
        # Create new research.md with Section 3
        new_content = "# Research Documentation\n\n" + section3_content
    
    research_path.write_text(new_content)
    print(f"✓ Power analysis report written to research.md Section 3")
    print(f"✓ Constraint mismatch documented: n={N_ACTUAL} vs required n≥{N_REQUIRED}")
    
    # Also save raw report to state for verification
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    report_path = state_dir / "power_analysis_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"✓ Raw report saved to {report_path}")

if __name__ == "__main__":
    main()
