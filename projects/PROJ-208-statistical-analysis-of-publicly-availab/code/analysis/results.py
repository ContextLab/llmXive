"""
Results text generation module for User Story 3.

This module enforces the constitutional requirement (FR-008) that all generated
result text must use "associational" or "correlational" language, avoiding
causal claims.

It provides utilities to generate text summaries from statistical outputs
(ANOVA, Mixed Effects, Collinearity, Sensitivity) with strict language enforcement.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Import configuration
from utils.config import get_config

# Setup logging
logger = logging.getLogger(__name__)

# Forbidden causal phrases to detect and replace
CAUSAL_PHRASES = [
    "causes", "caused by", "determines", "determined by",
    "leads to", "results in", "influences"
]

# Allowed associational phrases
ASSOCIATIONAL_PHRASES = [
    "is associated with", "is correlated with", "shows an association with",
    "is linked to", "co-occurs with", "is related to"
]

def sanitize_text(text: str) -> str:
    """
    Sanitize text to ensure it uses associational language.
    Replaces causal phrases with associational ones.

    Args:
        text: The raw text string to sanitize.

    Returns:
        Sanitized text with causal language replaced.
    """
    if not text:
        return ""

    sanitized = text
    for causal in CAUSAL_PHRASES:
        # Case-insensitive replacement
        lower_causal = causal.lower()
        if lower_causal in sanitized.lower():
            # Map to a generic associational phrase
            replacement = ASSOCIATIONAL_PHRASES[0]
            sanitized = sanitized.replace(causal, replacement)
            sanitized = sanitized.replace(causal.capitalize(), replacement.capitalize())
            sanitized = sanitized.replace(causal.upper(), replacement.upper())

    return sanitized

def generate_kruskal_wallis_summary(stats: Dict[str, Any], p_value: float, alpha: float = 0.05) -> str:
    """
    Generate a text summary for Kruskal-Wallis test results.
    Enforces associational language.

    Args:
        stats: Dictionary containing test statistics (H, df, etc.)
        p_value: The p-value from the test
        alpha: Significance level

    Returns:
        Formatted text summary string.
    """
    h_stat = stats.get('h_statistic', 0.0)
    df = stats.get('df', 0)

    significance_text = "significant" if p_value < alpha else "not significant"
    
    # Base sentence using allowed language
    summary = (
        f"The Kruskal-Wallis test indicates that resolution times {significance_text} "
        f"associated with programming language groups (H={h_stat:.2f}, df={df}, "
        f"p-value={p_value:.4f}). This suggests a correlational relationship between "
        f"language choice and issue resolution duration, but does not imply causation."
    )

    return sanitize_text(summary)

def generate_pairwise_summary(comparisons: List[Dict[str, Any]], alpha: float = 0.05) -> str:
    """
    Generate a text summary for pairwise comparisons with Holm-Bonferroni correction.
    Enforces associational language.

    Args:
        comparisons: List of comparison dictionaries (group1, group2, p_value, significant)
        alpha: Significance level

    Returns:
        Formatted text summary string.
    """
    significant_pairs = [c for c in comparisons if c.get('significant', False)]
    
    if not significant_pairs:
        return (
            "No pairwise comparisons between programming language groups showed "
            "a significant association after Holm-Bonferroni correction. "
            "This indicates that any observed differences in resolution times "
            "are correlational and not statistically distinguishable from chance."
        )

    summary_parts = [
        f"After Holm-Bonferroni correction, {len(significant_pairs)} pairwise comparisons "
        "showed a significant association between language groups and resolution times."
    ]

    for comp in significant_pairs:
        g1 = comp.get('group1', 'Unknown')
        g2 = comp.get('group2', 'Unknown')
        p_val = comp.get('p_value', 0.0)
        summary_parts.append(
            f"  - {g1} vs {g2}: p={p_val:.4f} (associated difference in resolution times)"
        )

    summary_parts.append(
        "These findings represent correlational patterns in the data."
    )

    return sanitize_text("\n".join(summary_parts))

def generate_lme_summary(fixed_effects: Dict[str, Any], random_effects: Dict[str, Any]) -> str:
    """
    Generate a text summary for Linear Mixed Effects model results.
    Enforces associational language.

    Args:
        fixed_effects: Dictionary of fixed effect coefficients and stats
        random_effects: Dictionary of random effect variances

    Returns:
        Formatted text summary string.
    """
    summary = [
        "The linear mixed-effects model reveals associations between predictors "
        "and issue resolution times. The fixed effects indicate that changes in "
        "predictor variables are correlated with changes in resolution duration."
    ]

    if fixed_effects:
        summary.append("Fixed effects summary:")
        for var, stats in fixed_effects.items():
            coef = stats.get('coef', 0.0)
            p_val = stats.get('p_value', 1.0)
            summary.append(
                f"  - {var}: coefficient={coef:.4f}, p={p_val:.4f} "
                f"(associational link to resolution time)"
            )

    if random_effects:
        repo_var = random_effects.get('repo_variance', 0.0)
        summary.append(
            f"Random intercept variance for repositories: {repo_var:.4f}. "
            "This indicates that resolution times are associated with specific "
            "repositories, suggesting correlational patterns at the repository level."
        )

    summary.append(
        "Note: These results describe correlational relationships and should not "
        "be interpreted as causal effects."
    )

    return sanitize_text("\n".join(summary))

def generate_collinearity_summary(vif_results: Dict[str, Any]) -> str:
    """
    Generate a text summary for collinearity diagnostics.
    Enforces associational language.

    Args:
        vif_results: Dictionary containing VIF scores and flags

    Returns:
        Formatted text summary string.
    """
    high_vif_vars = [v for v, score in vif_results.get('vif_scores', {}).items() if score >= 5.0]
    
    if high_vif_vars:
        summary = (
            f"High Variance Inflation Factors (VIF ≥ 5) were detected for variables: "
            f"{', '.join(high_vif_vars)}. This indicates that these predictors are "
            "correlated with each other, suggesting a joint associational relationship "
            "with the outcome rather than independent effects. "
            "The model coefficients describe these combined correlational patterns."
        )
    else:
        summary = (
            "No significant multicollinearity was detected (all VIF < 5). "
            "Predictors show weak correlational relationships with each other, "
            "allowing for more distinct associational interpretations of individual effects."
        )

    return sanitize_text(summary)

def generate_sensitivity_summary(sensitivity_data: Dict[str, Any]) -> str:
    """
    Generate a text summary for sensitivity analysis results.
    Enforces associational language.

    Args:
        sensitivity_data: Dictionary containing sensitivity metrics across cutoffs

    Returns:
        Formatted text summary string.
    """
    cutoffs = sensitivity_data.get('cutoffs', [])
    fp_rates = sensitivity_data.get('false_positive_rates', [])
    fn_rates = sensitivity_data.get('false_negative_rates', [])

    if not cutoffs:
        return "No sensitivity analysis data available."

    summary = [
        "Sensitivity analysis across different resolution time cutoffs reveals "
        "how the associational strength between predictors and outcomes varies "
        "with threshold selection."
    ]

    summary.append("Threshold Sensitivity Summary:")
    for i, cutoff in enumerate(cutoffs):
        fp = fp_rates[i] if i < len(fp_rates) else 0.0
        fn = fn_rates[i] if i < len(fn_rates) else 0.0
        summary.append(
            f"  - Cutoff {cutoff:.1f}h: FP rate={fp:.2%}, FN rate={fn:.2%} "
            f"(associational stability at this threshold)"
        )

    summary.append(
        "These results demonstrate that the observed correlational patterns "
        "are sensitive to the chosen definition of 'fast' vs 'slow' resolution."
    )

    return sanitize_text("\n".join(summary))

def generate_full_report(
    kw_summary: str,
    pairwise_summary: str,
    lme_summary: str,
    collinearity_summary: str,
    sensitivity_summary: str,
    output_path: Path
) -> None:
    """
    Generate and save a full results report with enforced associational language.

    Args:
        kw_summary: Kruskal-Wallis summary text
        pairwise_summary: Pairwise comparison summary text
        lme_summary: Mixed effects model summary text
        collinearity_summary: Collinearity diagnostics summary text
        sensitivity_summary: Sensitivity analysis summary text
        output_path: Path to save the JSON report
    """
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "language_policy": "associational_only",
        "sections": {
            "kruskal_wallis": kw_summary,
            "pairwise_comparisons": pairwise_summary,
            "mixed_effects_model": lme_summary,
            "collinearity_diagnostics": collinearity_summary,
            "sensitivity_analysis": sensitivity_summary
        }
    }

    # Validate that no causal language remains (sanity check)
    full_text = json.dumps(report)
    for causal in CAUSAL_PHRASES:
        if causal.lower() in full_text.lower():
            logger.warning(f"Potential causal language '{causal}' detected in report. Review needed.")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Results report saved to {output_path}")

def main():
    """
    Main entry point for generating results text.
    This function is a placeholder for execution if called directly,
    but the primary usage is importing the generation functions.
    """
    config = get_config()
    output_path = Path(config.get_path("data_processed")) / "results_summary.json"
    
    # Dummy data for demonstration if run directly
    # In real execution, these would be populated by upstream tasks
    kw_stats = {'h_statistic': 12.5, 'df': 4}
    kw_p = 0.015
    comparisons = [
        {'group1': 'Python', 'group2': 'JavaScript', 'p_value': 0.02, 'significant': True},
        {'group1': 'Python', 'group2': 'C++', 'p_value': 0.45, 'significant': False}
    ]
    fixed_effects = {'issue_count': {'coef': 0.5, 'p_value': 0.01}}
    random_effects = {'repo_variance': 0.8}
    vif_results = {'vif_scores': {'issue_count': 6.2, 'comments': 1.5}}
    sensitivity_data = {
        'cutoffs': [24, 48, 72],
        'false_positive_rates': [0.1, 0.05, 0.02],
        'false_negative_rates': [0.05, 0.1, 0.2]
    }

    kw_sum = generate_kruskal_wallis_summary(kw_stats, kw_p)
    pair_sum = generate_pairwise_summary(comparisons)
    lme_sum = generate_lme_summary(fixed_effects, random_effects)
    coll_sum = generate_collinearity_summary(vif_results)
    sens_sum = generate_sensitivity_summary(sensitivity_data)

    generate_full_report(kw_sum, pair_sum, lme_sum, coll_sum, sens_sum, output_path)

if __name__ == "__main__":
    main()
