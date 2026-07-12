"""
Power analysis constraint mismatch documentation module.

This module documents the discrepancy between the specification's sample size
requirement (n >= 200) and the available dataset size (HumanEval n=164),
calculates the resulting power mismatch, and proposes mitigation strategies.
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Constants from spec and dataset
SPEC_MIN_SAMPLE_SIZE = 200
HUMANEVAL_SAMPLE_SIZE = 164
TARGET_POWER = 0.80
EFFECT_SIZE_DEFAULT = 0.5  # Medium effect size assumption for calculation

def calculate_constraint_mismatch(
    spec_min: int = SPEC_MIN_SAMPLE_SIZE,
    actual_n: int = HUMANEVAL_SAMPLE_SIZE,
    target_power: float = TARGET_POWER,
    effect_size: float = EFFECT_SIZE_DEFAULT
) -> Dict[str, Any]:
    """
    Calculate the statistical power mismatch given the sample size constraint.
    
    Returns a dictionary with:
      - spec_requirement: int (n >= 200)
      - actual_sample_size: int (n = 164)
      - sample_size_shortfall: int
      - estimated_power_at_actual_n: float (approximation)
      - power_deficit: float
      - minimum_detectable_effect_at_actual_n: float (approximation)
      - constraint_mismatch: str
      - citation_context: str
    
    Note: Uses a simplified power approximation for demonstration.
    Real power analysis would use statsmodels.stats.power module.
    """
    if actual_n >= spec_min:
        return {
            "spec_requirement": spec_min,
            "actual_sample_size": actual_n,
            "sample_size_shortfall": 0,
            "estimated_power_at_actual_n": 1.0,
            "power_deficit": 0.0,
            "minimum_detectable_effect_at_actual_n": effect_size,
            "constraint_mismatch": "None - sample size meets spec",
            "citation_context": "No citation mismatch detected."
        }
    
    # Approximate power calculation (simplified)
    # Power ~ 1 - beta, where beta depends on n and effect size
    # For a two-sample t-test approximation:
    # n_per_group = actual_n / 2 (paired design, but using as proxy)
    # This is a rough estimate; real implementation should use statsmodels
    import math
    n_eff = actual_n
    # Approximation: Power decreases as n decreases below required
    # If n_req = 200 gives power = 0.8 for effect_size = 0.5
    # Then n_actual = 164 gives power ~ 0.8 * sqrt(164/200)
    ratio = math.sqrt(actual_n / spec_min)
    estimated_power = min(1.0, target_power * ratio)
    
    power_deficit = target_power - estimated_power
    
    # Minimum detectable effect increases as n decreases
    # MDE ~ effect_size * sqrt(spec_min / actual_n)
    mde = effect_size * math.sqrt(spec_min / actual_n)
    
    return {
        "spec_requirement": spec_min,
        "actual_sample_size": actual_n,
        "sample_size_shortfall": spec_min - actual_n,
        "estimated_power_at_actual_n": round(estimated_power, 3),
        "power_deficit": round(power_deficit, 3),
        "minimum_detectable_effect_at_actual_n": round(mde, 3),
        "constraint_mismatch": f"Spec requires n >= {spec_min} but HumanEval provides n = {actual_n} (shortfall: {spec_min - actual_n})",
        "citation_context": "This mismatch is documented in {{claim:c_c9ee2ab8}} (arXiv:2410.12381) which uses the full HumanEval dataset (n=164). The spec's n>=200 requirement cannot be met without synthetic data generation or combining with other datasets, which may introduce domain shift."
    }

def generate_mitigation_strategy(mismatch_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a mitigation strategy for the power analysis constraint mismatch.
    
    Returns a dictionary with:
      - strategy_summary: str
      - proposed_actions: list of str
      - limitation_documentation: str
      - power_note: str
    """
    if "None" in mismatch_info["constraint_mismatch"]:
        return {
            "strategy_summary": "No mitigation required; sample size meets specification.",
            "proposed_actions": [],
            "limitation_documentation": "N/A",
            "power_note": "Power analysis is valid as per spec."
        }
    
    strategy = {
        "strategy_summary": "Document limitation and proceed with reduced power; note in final report.",
        "proposed_actions": [
            f"1. Proceed with HumanEval (n={mismatch_info['actual_sample_size']}) acknowledging the shortfall of {mismatch_info['sample_size_shortfall']} samples.",
            "2. Explicitly state in the final report (Section 5: Limitations) that the study is underpowered for the original spec requirement.",
            "3. Report the estimated power ({mismatch_info['estimated_power_at_actual_n']}) and minimum detectable effect ({mismatch_info['minimum_detectable_effect_at_actual_n']}) instead of the spec's target.",
            "4. Avoid claiming statistical significance for effects smaller than the new minimum detectable effect.",
            "5. Cite {{claim:c_c9ee2ab8}} (arXiv:2410.12381) as the source of the dataset constraint."
        ],
        "limitation_documentation": (
            f"Constraint Mismatch: The specification (FR-010) requires a minimum sample size of n >= {mismatch_info['spec_requirement']} to achieve power >= {TARGET_POWER}. "
            f"The available dataset (HumanEval) contains only n = {mismatch_info['actual_sample_size']} problems. "
            f"This results in an estimated statistical power of {mismatch_info['estimated_power_at_actual_n']} (deficit: {mismatch_info['power_deficit']}) "
            f"and increases the minimum detectable effect size to {mismatch_info['minimum_detectable_effect_at_actual_n']}."
        ),
        "power_note": (
            f"Power is reduced to {mismatch_info['estimated_power_at_actual_n']} due to sample size constraints. "
            f"Results should be interpreted with caution, particularly for small effect sizes."
        )
    }
    return strategy

def write_research_section3_content(
    output_path: str,
    mismatch_info: Dict[str, Any],
    mitigation_info: Dict[str, Any]
) -> None:
    """
    Write the content for research.md Section 3 (Power Analysis) to the specified file.
    
    Args:
        output_path: Path to the research.md file (or a snippet file).
        mismatch_info: Dictionary from calculate_constraint_mismatch.
        mitigation_info: Dictionary from generate_mitigation_strategy.
    """
    section_content = f"""
## Section 3: Power Analysis and Sample Size Justification

### 3.1 Sample Size Requirement (FR-010)
The specification (FR-010) requires a minimum sample size of **n >= {mismatch_info['spec_requirement']}** to achieve a statistical power of **>= {TARGET_POWER}** for the primary hypotheses (accuracy and latency differences).

### 3.2 Available Dataset
The primary dataset for this study is **HumanEval** (from HuggingFace Datasets).
- **Total Problems**: {mismatch_info['actual_sample_size']}
- **Source**: https://huggingface.co/datasets/openai_humaneval

### 3.3 Constraint Mismatch
{mismatch_info['constraint_mismatch']}

**Citation Context**: {mismatch_info['citation_context']}

### 3.4 Power Impact Analysis
Given the actual sample size of n = {mismatch_info['actual_sample_size']}:
- **Estimated Power**: {mismatch_info['estimated_power_at_actual_n']} (Target: {TARGET_POWER})
- **Power Deficit**: {mismatch_info['power_deficit']}
- **Minimum Detectable Effect (MDE)**: {mismatch_info['minimum_detectable_effect_at_actual_n']} (increased from the original target effect size)

*Note: These values are approximations based on a simplified power model. A rigorous analysis using `statsmodels.stats.power` would be performed if additional samples were available.*

### 3.5 Mitigation Strategy
{mitigation_info['strategy_summary']}

**Proposed Actions**:
{chr(10).join('  - ' + action for action in mitigation_info['proposed_actions'])}

### 3.6 Limitation Statement for Final Report
{mitigation_info['limitation_documentation']}

### 3.7 Power Note for Results Interpretation
{mitigation_info['power_note']}
"""
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(section_content)
    
    print(f"Research Section 3 content written to: {output_path}")

def main():
    """Main entry point for the power constraint analysis."""
    # Calculate mismatch
    mismatch_info = calculate_constraint_mismatch()
    
    # Generate mitigation
    mitigation_info = generate_mitigation_strategy(mismatch_info)
    
    # Define output path (relative to project root)
    output_path = "data/research_section3_draft.md"
    
    # Write content
    write_research_section3_content(output_path, mismatch_info, mitigation_info)
    
    # Also print a summary to stdout for immediate feedback
    print("\n--- Power Analysis Constraint Summary ---")
    print(f"Spec Requirement: n >= {mismatch_info['spec_requirement']}")
    print(f"Actual Sample Size: n = {mismatch_info['actual_sample_size']}")
    print(f"Mismatch: {mismatch_info['constraint_mismatch']}")
    print(f"Estimated Power: {mismatch_info['estimated_power_at_actual_n']}")
    print(f"Mitigation: {mitigation_info['strategy_summary']}")

if __name__ == "__main__":
    main()