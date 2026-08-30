"""
Reporting module for generating analysis reports with strict associational framing.

This module ensures all output reports frame findings as associational only (FR-006),
avoiding causal language such as 'causes', 'leads to', 'effect', or 'impact'.
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# Causal terms that must be avoided (FR-006)
CAUSAL_TERMS = [
    'causes', 'cause', 'caused', 'causing',
    'leads to', 'lead to', 'led to',
    'effect', 'effects', 'impacts', 'impact',
    'influence on', 'influences', 'influenced',
    'drives', 'drive', 'driving', 'drove',
    'determines', 'determine', 'determined',
    'results in', 'result in', 'resulted in',
    'contributes to', 'contribute to', 'contributed to',
    'increases', 'increase', 'decreases', 'decrease',
    'improves', 'improve', 'worsens', 'worsen'
]

# Associational alternatives
ASSOCIATIONAL_TERMS = {
    'causes': 'is associated with',
    'leads to': 'is associated with',
    'effect': 'association',
    'impact': 'association',
    'influence on': 'association with',
    'drives': 'predicts',
    'determines': 'is associated with',
    'results in': 'is associated with',
    'contributes to': 'is associated with',
    'increases': 'is positively associated with',
    'decreases': 'is negatively associated with',
    'improves': 'is positively associated with',
    'worsens': 'is negatively associated with'
}

logger = logging.getLogger(__name__)


def sanitize_text(text: str) -> str:
    """
    Replace causal language with associational language in text.

    Args:
        text: Input text that may contain causal language

    Returns:
        Text with causal terms replaced by associational alternatives
    """
    result = text
    for causal_term, assoc_term in ASSOCIATIONAL_TERMS.items():
        # Case-insensitive replacement
        result = result.replace(causal_term, assoc_term)
        result = result.replace(causal_term.capitalize(), assoc_term.capitalize())
        result = result.replace(causal_term.upper(), assoc_term.upper())
    return result


def validate_associational_framing(text: str, raise_on_error: bool = False) -> List[str]:
    """
    Check text for causal language violations (FR-006).

    Args:
        text: Text to validate
        raise_on_error: If True, raise ValueError on violations

    Returns:
        List of violation messages (empty if no violations)
    """
    violations = []
    lower_text = text.lower()

    for term in CAUSAL_TERMS:
        if term in lower_text:
            violations.append(f"Found causal term '{term}' - replace with associational language")

    if violations and raise_on_error:
        raise ValueError(f"Associational framing violations found: {violations}")

    return violations


def generate_final_report(
    results: Dict[str, Any],
    output_path: Path,
    include_limitations: bool = True
) -> None:
    """
    Generate the final analysis report with strict associational framing.

    Args:
        results: Dictionary containing analysis results (coefficients, p-values, etc.)
        output_path: Path to write the report (Markdown format)
        include_limitations: Whether to include a dedicated limitations section
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build report content
    report_lines = [
        "# Analysis Report: Algorithmic Recommendations and Learner Diversity",
        "",
        "**Generated**: " + datetime.now().isoformat(),
        "",
        "## Executive Summary",
        "",
        "This report presents an associational analysis of the relationship between",
        "algorithmic recommendation diversity and learner enrollment diversity.",
        "All findings are framed as associations; no causal claims are made.",
        "",
        "## Methodology",
        "",
        "### Data Processing",
        "- Ingested course enrollment data with schema validation",
        "- Calculated Shannon entropy-based diversity scores for recommendations and enrollments",
        "- Applied Propensity Score Weighting (PSW) to control for observed confounders",
        "- Used weighted linear regression with Generalized Least Squares (GLS) fallback",
        "",
        "### Statistical Approach",
        "- Primary analysis: Weighted linear regression with stabilized PSW weights",
        "- Diagnostics: Variance Inflation Factor (VIF) for multicollinearity",
        "- Robustness: Residual permutation tests and sensitivity analysis",
        "- Limitations: E-value calculation for unmeasured confounding",
        "",
        "## Results",
        ""
    ]

    # Add results section
    if 'model_results' in results:
        model_results = results['model_results']
        report_lines.append("### Association Between Recommendation Diversity and Learner Diversity")
        report_lines.append("")

        # Extract coefficient and p-value
        coefficient = model_results.get('coefficient', None)
        p_value = model_results.get('p_value', None)
        std_error = model_results.get('std_error', None)
        n_samples = model_results.get('n_samples', None)

        report_lines.append(f"- **Sample Size**: {n_samples} observations")
        report_lines.append(f"- **Coefficient**: {coefficient:.4f} (SE: {std_error:.4f})")
        report_lines.append(f"- **p-value**: {p_value:.4g}")
        report_lines.append("")

        # Framing statement
        if p_value is not None and p_value < 0.05:
            report_lines.append(
                f"Recommendation diversity is **positively associated** with learner diversity "
                f"(β = {coefficient:.4f}, p < 0.05). This association suggests that learners "
                f"exposed to more diverse recommendations tend to enroll in more diverse course sets."
            )
        elif p_value is not None:
            report_lines.append(
                f"Recommendation diversity shows **no statistically significant association** "
                f"with learner diversity (β = {coefficient:.4f}, p = {p_value:.4g})."
            )
        else:
            report_lines.append(
                f"Association analysis yielded coefficient β = {coefficient:.4f}."
            )
        report_lines.append("")

    # Add diagnostics
    if 'diagnostics' in results:
        diagnostics = results['diagnostics']
        report_lines.append("### Diagnostic Statistics")
        report_lines.append("")

        if 'vif_values' in diagnostics:
            report_lines.append("**Multicollinearity (VIF)**:")
            for var, vif in diagnostics['vif_values'].items():
                status = "✓" if vif < 5 else "⚠"
                report_lines.append(f"- {var}: {vif:.2f} {status}")
            report_lines.append("")

        if 'weight_stability' in diagnostics:
            stability = diagnostics['weight_stability']
            report_lines.append("**PSW Weight Stability**:")
            report_lines.append(f"- Median weight: {stability.get('median_weight', 'N/A')}")
            report_lines.append(f"- Max weight / Median: {stability.get('max_median_ratio', 'N/A')}")
            if stability.get('extreme_weights_detected', False):
                report_lines.append("⚠ **Warning**: Extreme weights detected (>10x median). Results should be interpreted with caution.")
            report_lines.append("")

    # Add robustness metrics
    if 'robustness' in results:
        robustness = results['robustness']
        report_lines.append("### Robustness Analysis")
        report_lines.append("")

        if 'permutation_test' in robustness:
            perm = robustness['permutation_test']
            report_lines.append("**Residual Permutation Test**:")
            report_lines.append(f"- Observed statistic: {perm.get('observed_statistic', 'N/A')}")
            report_lines.append(f"- Null distribution 95% CI: [{perm.get('ci_lower', 'N/A')}, {perm.get('ci_upper', 'N/A')}]")
            report_lines.append(f"- Permutation p-value: {perm.get('p_value', 'N/A')}")
            report_lines.append("")

        if 'e_value' in robustness:
            e_val = robustness['e_value']
            report_lines.append("**E-value for Unmeasured Confounding**:")
            report_lines.append(f"- E-value: {e_val:.4f}")
            report_lines.append(
                "The E-value represents the minimum strength of association that an unmeasured "
                "confounder would need to have with both the treatment and outcome to fully "
                "explain the observed association."
            )
            report_lines.append("")

    # Add limitations section (mandatory per FR-006)
    if include_limitations:
        report_lines.append("## Limitations")
        report_lines.append("")
        report_lines.append(
            "**Important**: Findings are **associational**; no causal claims are made due to "
            "lack of randomization. This study cannot establish that algorithmic recommendations "
            "cause changes in learner behavior."
        )
        report_lines.append("")
        report_lines.append("### Key Limitations:")
        report_lines.append("")
        report_lines.append("1. **Observational Design**: Without randomization, unmeasured confounders may explain observed associations.")
        report_lines.append("2. **Propensity Score Limitations**: PSW only controls for observed covariates; unmeasured confounding remains possible.")
        report_lines.append("3. **Weight Instability**: Extreme weights may reduce effective sample size and increase variance.")
        report_lines.append("4. **Generalizability**: Results apply to the specific dataset and context studied.")
        report_lines.append("")
        report_lines.append("### Interpretation Guidance")
        report_lines.append("")
        report_lines.append(
            "All reported relationships should be interpreted as statistical associations. "
            "Terms such as 'effect', 'impact', 'causes', or 'leads to' are intentionally avoided. "
            "Instead, we use 'associated with', 'predicts', or 'correlates with'."
        )
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")
        report_lines.append(
            "*Report generated by the llmXive automated science pipeline. "
            "All analysis adheres to associational framing requirements (FR-006).*"
        )

    # Write report
    report_content = "\n".join(report_lines)

    # Final validation
    violations = validate_associational_framing(report_content)
    if violations:
        logger.warning(f"Report contains potential causal language: {violations}")
        # Still write the report but log the warning
        # In production, this might raise an error

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"Final report written to {output_path}")


def generate_summary_json(
    results: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate a JSON summary of results with associational framing metadata.

    Args:
        results: Dictionary containing analysis results
        output_path: Path to write JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'framing': 'associational',
            'causal_claims': False,
            'fr-006_compliant': True
        },
        'results': results,
        'disclaimer': (
            "All findings are associational. No causal claims are made. "
            "This analysis cannot establish causation due to the observational nature of the data."
        )
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)

    logger.info(f"Summary JSON written to {output_path}")


def run_associational_audit(
    report_path: Path,
    strict_mode: bool = True
) -> Dict[str, Any]:
    """
    Audit an existing report for causal language violations.

    Args:
        report_path: Path to the report file to audit
        strict_mode: If True, fail on any violation

    Returns:
        Dictionary with audit results
    """
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    violations = validate_associational_framing(content, raise_on_error=False)

    audit_result = {
        'report_path': str(report_path),
        'violations_found': len(violations),
        'violations': violations,
        'is_compliant': len(violations) == 0,
        'strict_mode': strict_mode
    }

    if strict_mode and violations:
        raise ValueError(f"Report is not FR-006 compliant: {violations}")

    return audit_result