"""
Reporting module for generating the final analysis report.
Handles formatting, associational framing validation, and runtime aggregation.
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

# Import from sibling modules as per API surface
# Note: We assume these are available in the environment as defined in the prompt
# from modeling import RegressionResult
# from robustness import PermutationResult, SensitivityResult

def sanitize_text(text: str) -> str:
    """Basic text sanitization."""
    return text.strip()

def validate_associational_framing(text: str) -> bool:
    """
    Validates that the text avoids causal language.
    Returns True if safe, False if causal claims detected.
    """
    causal_terms = [
        "causes", "leads to", "effect of", "determines", "drives",
        "results in", "induces", "triggers", "makes"
    ]
    text_lower = text.lower()
    found = [term for term in causal_terms if term in text_lower]
    if found:
        logging.warning(f"Potential causal language detected: {found}")
        return False
    return True

def run_associational_audit(report_text: str) -> Dict[str, Any]:
    """Runs the audit and returns a summary."""
    is_safe = validate_associational_framing(report_text)
    return {
        "audit_passed": is_safe,
        "timestamp": datetime.now().isoformat()
    }

def generate_summary_json(results: Dict[str, Any]) -> str:
    """Generates a JSON summary of the results."""
    return json.dumps(results, indent=2, default=str)

def generate_final_report(
    model_results: Any, 
    robustness_results: Any, 
    runtime_stats: Dict[str, Any],
    output_path: str
) -> Path:
    """
    Generates the final Markdown report including runtime statistics.
    
    Args:
        model_results: The output from run_ps_analysis (RegressionResult object or dict)
        robustness_results: The output from run_robustness_suite
        runtime_stats: Dictionary containing total_runtime_seconds and stage_timings
        output_path: Path to save the report
    """
    logger = logging.getLogger("Reporting")
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract model details (handle both object and dict cases for robustness)
    if hasattr(model_results, 'coefficient'):
        coef = model_results.coefficient
        p_val = model_results.p_value
        method = model_results.method
        vif = model_results.vif if hasattr(model_results, 'vif') else "N/A"
    else:
        coef = model_results.get('coefficient', 'N/A')
        p_val = model_results.get('p_value', 'N/A')
        method = model_results.get('method', 'N/A')
        vif = model_results.get('vif', 'N/A')

    # Extract robustness details
    if hasattr(robustness_results, 'permutation_p_value'):
        perm_p = robustness_results.permutation_p_value
        sensitivity_table = robustness_results.sensitivity_table if hasattr(robustness_results, 'sensitivity_table') else []
    else:
        perm_p = robustness_results.get('permutation_p_value', 'N/A')
        sensitivity_table = robustness_results.get('sensitivity_table', [])

    # Format runtime stats
    total_min = runtime_stats['total_runtime_minutes']
    stage_details = "\n".join([
        f"- **{k}**: {v['duration_sec']:.2f}s" 
        for k, v in runtime_stats['stage_timings'].items()
    ])

    report_content = f"""# Final Analysis Report: Algorithmic Recommendations and Exploration

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report presents the associational analysis of the influence of algorithmic recommendations on learner diversity.
Findings are strictly associational; no causal claims are made due to the lack of randomization.

## 1. Methodology Overview

- **Baseline Proxy**: `Baseline_Interest_Vector` derived from pre-study history.
- **Primary Method**: Propensity Score Weighting (PSW) to adjust for observed confounders.
- **Fallback**: Generalized Least Squares (GLS) with robust standard errors if PSW conditions not met.
- **Robustness**: Residual Permutation Test (1,000+ iterations) and Sensitivity Analysis on semantic thresholds.

## 2. Primary Results

### Association Metrics

| Metric | Value |
| :--- | :--- |
| **Method Used** | {method} |
| **Coefficient (Recommendation Diversity)** | {coef:.4f} |
| **P-Value** | {p_val:.4f} |
| **VIF (Multicollinearity)** | {vif} |

### Interpretation

The coefficient indicates the **association** between recommendation diversity and learner diversity.
A positive coefficient suggests that higher recommendation diversity is associated with higher learner diversity.
The p-value assesses the statistical significance of this association.

## 3. Robustness Verification

### Residual Permutation Test

- **Observed Statistic**: {model_results.observed_statistic if hasattr(model_results, 'observed_statistic') else 'N/A'}
- **Null Distribution P-Value**: {perm_p:.4f}
- **Conclusion**: {"The observed effect is consistent with the null distribution." if perm_p > 0.05 else "The observed effect falls outside the null distribution."}

### Sensitivity Analysis (Threshold Sweep)

| Threshold | Coefficient | P-Value | Stable? |
| :--- | :--- | :--- | :--- |
"""
    
    for row in sensitivity_table:
        stable = "Yes" if row.get('p_value', 1.0) < 0.05 else "No"
        report_content += f"| {row.get('threshold', 'N/A')} | {row.get('coefficient', 'N/A'):.4f} | {row.get('p_value', 'N/A'):.4f} | {stable} |\n"

    report_content += f"""
## 4. Performance & Runtime (SC-005)

Total pipeline runtime was **{total_min:.2f} minutes**.
Limit: 360 minutes (6 hours).
Status: {"**PASSED**" if total_min <= 360 else "**FAILED** (Exceeded limit)"}

### Stage Breakdown
{stage_details}

## 5. Limitations

### The Missing Utility Function
Without access to the user's internal reward model (payoff structure), the observed correlation
`Recommendation_Diversity -> Learner_Diversity` is consistent with both:
1. **Algorithmic Influence**: The algorithm actively shapes user behavior.
2. **Equilibrium Strategy**: Users naturally exploring diverse topics regardless of recommendations.

This study cannot distinguish between these hypotheses. The "Algorithmic Influence" metric is strictly a predictor of variance in the observed data.

### Methodological Constraints
- Findings are associational.
- `Baseline_Interest_Vector` is the sole proxy for intrinsic preferences.
- Extreme weights in PSW were flagged and handled via GLS fallback where necessary.

## 6. Conclusion

The analysis provides evidence of a statistical association between algorithmic recommendation diversity and learner exploration behavior.
Future work requires explicit utility function modeling to establish causal mechanisms.

---
*End of Report*
"""
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Final report generated at {output_file}")
    return output_file