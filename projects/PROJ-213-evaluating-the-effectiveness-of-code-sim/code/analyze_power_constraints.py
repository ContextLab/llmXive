"""
Module: analyze_power_constraints.py

Purpose:
Document the power analysis constraint mismatch where the project's available
sample size (HumanEval n=164) contradicts the specification requirement (n>=200).
This module calculates the mismatch metrics and generates the mitigation strategy
to be included in research.md Section 3.

API:
- calculate_constraint_mismatch(spec_n, actual_n, power_target, effect_size)
- generate_mitigation_strategy(mismatch_data)
- write_research_section3_content(mismatch_data, mitigation_data, output_path)
- main()
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Constants based on project context and external claim
# Claim: 2410.12381 (arXiv:2410.12381) - "The Effect of Code Simplification on LLM Performance"
# This claim establishes that HumanEval is the standard benchmark with fixed size n=164.
CLAIM_URL = "https://arxiv.org/abs/2410.12381"
CLAIM_ID = "2410.12381"
CLAIM_TITLE = "The Effect of Code Simplification on LLM Performance"

# Specification requirement
SPEC_MIN_N = 200
PROJECT_ACTUAL_N = 164  # HumanEval full set size
POWER_TARGET = 0.80
EFFECT_SIZE = 0.5  # Medium effect size assumption for calculation

def calculate_constraint_mismatch(spec_n: int, actual_n: int, power_target: float, effect_size: float) -> Dict[str, Any]:
    """
    Calculates the statistical implications of the sample size mismatch.
    
    Args:
        spec_n: Required sample size from spec (200)
        actual_n: Available sample size (164)
        power_target: Target statistical power (0.8)
        effect_size: Assumed effect size for calculation (0.5)
        
    Returns:
        Dictionary containing mismatch details and statistical impact.
    """
    if actual_n >= spec_n:
        return {
            "mismatch_detected": False,
            "message": "Sample size meets specification."
        }

    # Estimate power reduction (simplified approximation for documentation)
    # Power scales roughly with sqrt(n). 
    # Power_actual ~ Power_target * sqrt(actual_n / spec_n)
    # This is an approximation to demonstrate the "reduced power" concept.
    import math
    power_ratio = math.sqrt(actual_n / spec_n)
    estimated_actual_power = power_target * power_ratio
    
    # Calculate minimum detectable effect (MDE) increase required to maintain power
    # MDE is inversely proportional to sqrt(n). 
    # MDE_actual ~ MDE_spec * sqrt(spec_n / actual_n)
    mde_multiplier = math.sqrt(spec_n / actual_n)
    
    return {
        "mismatch_detected": True,
        "spec_requirement": spec_n,
        "actual_available": actual_n,
        "deficit": spec_n - actual_n,
        "deficit_percentage": round(((spec_n - actual_n) / spec_n) * 100, 2),
        "original_target_power": power_target,
        "estimated_actual_power": round(estimated_actual_power, 3),
        "power_reduction_factor": round(power_ratio, 3),
        "mde_multiplier": round(mde_multiplier, 3),
        "interpretation": f"With n={actual_n} instead of n={spec_n}, statistical power drops from {power_target} to approx {estimated_actual_power:.3f} for effect size {effect_size}. Minimum Detectable Effect increases by factor {mde_multiplier:.3f}."
    }

def generate_mitigation_strategy(mismatch_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a mitigation strategy for the power analysis constraint mismatch.
    
    Strategy:
    1. Document limitation in final report.
    2. Note reduced power in conclusions.
    3. Use HumanEval as-is (cannot expand dataset without changing benchmark).
    4. Emphasize effect size estimation over binary significance if power is low.
    
    Args:
        mismatch_data: Output from calculate_constraint_mismatch
        
    Returns:
        Dictionary with mitigation steps and documentation requirements.
    """
    if not mismatch_data.get("mismatch_detected"):
        return {"mitigation_required": False}

    return {
        "mitigation_required": True,
        "strategy": [
            "1. Explicitly document the constraint mismatch in the final report (Section: Limitations).",
            "2. Note that statistical power is reduced to approx {:.3f} (target was 0.80).".format(mismatch_data["estimated_actual_power"]),
            "3. Interpret results with caution; avoid claiming 'no effect' for non-significant findings due to low power.",
            "4. Report effect sizes and confidence intervals alongside p-values.",
            "5. Acknowledge that the HumanEval benchmark (n=164) is the standard fixed set per claim {}.".format(CLAIM_ID),
            "6. Propose future work using larger synthetic benchmarks if higher power is required."
        ],
        "report_additions": {
            "section": "Limitations and Future Work",
            "content_snippet": "The study utilizes the HumanEval benchmark (n=164), which is below the specification requirement of n>=200 (FR-010). This results in a statistical power of approximately {:.3f} for a medium effect size (0.5), reducing the ability to detect small effects. Findings should be interpreted as exploratory for effects smaller than the minimum detectable effect at this power level.".format(mismatch_data["estimated_actual_power"])
        },
        "citation": {
            "id": CLAIM_ID,
            "url": CLAIM_URL,
            "title": CLAIM_TITLE,
            "relevance": "Establishes HumanEval as the standard fixed benchmark of 164 problems."
        }
    }

def write_research_section3_content(mismatch_data: Dict[str, Any], mitigation_data: Dict[str, Any], output_path: str) -> None:
    """
    Writes the content for research.md Section 3 (Power Analysis & Constraints).
    
    Args:
        mismatch_data: Data from calculate_constraint_mismatch
        mitigation_data: Data from generate_mitigation_strategy
        output_path: Path to research.md (or a section file)
    """
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    
    section_content = f"""
## Section 3: Power Analysis and Constraint Justification

**Date Generated**: {timestamp}

### 3.1 Sample Size Justification

**Specification Requirement (FR-010)**: Minimum sample size `n >= 200` to achieve statistical power >= 0.80 for medium effect sizes.

**Available Dataset**: HumanEval (Standard Benchmark)
- **Source**: {CLAIM_ID} ({CLAIM_URL})
- **Sample Size**: n = {PROJECT_ACTUAL_N}
- **Constraint**: The HumanEval benchmark is a fixed, standard set of 164 problems. Expanding this specific benchmark is not feasible without altering the evaluation standard.

### 3.2 Constraint Mismatch Analysis

**Mismatch Detected**: Yes
- **Required (Spec)**: {mismatch_data['spec_requirement']}
- **Available (Actual)**: {mismatch_data['actual_available']}
- **Deficit**: {mismatch_data['deficit']} problems ({mismatch_data['deficit_percentage']}% shortfall)

**Statistical Impact**:
- **Target Power**: {mismatch_data['original_target_power']}
- **Estimated Actual Power**: {mismatch_data['estimated_actual_power']} (for effect size 0.5)
- **Power Reduction Factor**: {mismatch_data['power_reduction_factor']}
- **MDE Multiplier**: {mismatch_data['mde_multiplier']} (Minimum Detectable Effect increases by this factor)

**Interpretation**:
{mismatch_data['interpretation']}

### 3.3 Mitigation Strategy

Given the constraint that the benchmark size is fixed at 164, the following mitigation strategies are adopted:

1. **Documentation**: Explicitly document this limitation in the final report.
2. **Power Adjustment**: Acknowledge reduced power (~{mismatch_data['estimated_actual_power']:.3f}) in conclusions.
3. **Statistical Approach**: Prioritize effect size estimation and confidence intervals over binary significance testing.
4. **Citation**: Reference {CLAIM_ID} as the authority on the HumanEval benchmark size.

**Proposed Mitigation Steps**:
{chr(10).join(['- ' + step for step in mitigation_data['strategy']])}

**Report Additions**:
> "The study utilizes the HumanEval benchmark (n={PROJECT_ACTUAL_N}), which is below the specification requirement of n>={SPEC_MIN_N} (FR-010). This results in a statistical power of approximately {mismatch_data['estimated_actual_power']:.3f} for a medium effect size (0.5), reducing the ability to detect small effects. Findings should be interpreted with this limitation in mind."

### 3.4 Conclusion

The project proceeds with n={PROJECT_ACTUAL_N} due to the fixed nature of the HumanEval benchmark. The analysis will be conducted with the understanding of reduced power, and results will be framed accordingly to avoid over-interpretation of non-significant findings.
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(section_content)

def main():
    """
    Main entry point to execute the power constraint analysis and write to research.md.
    """
    print("Starting Power Constraint Analysis (T003a)...")
    
    # Calculate mismatch
    mismatch_data = calculate_constraint_mismatch(
        spec_n=SPEC_MIN_N,
        actual_n=PROJECT_ACTUAL_N,
        power_target=POWER_TARGET,
        effect_size=EFFECT_SIZE
    )
    
    # Generate mitigation
    mitigation_data = generate_mitigation_strategy(mismatch_data)
    
    # Define output path
    research_md_path = "specs/001-eval-code-simplification/research.md"
    
    # Write content
    write_research_section3_content(mismatch_data, mitigation_data, research_md_path)
    
    print(f"Successfully wrote Section 3 content to {research_md_path}")
    print(f"Mismatch Status: {'Detected' if mismatch_data['mismatch_detected'] else 'None'}")
    print(f"Estimated Power: {mismatch_data.get('estimated_actual_power', 'N/A')}")

if __name__ == "__main__":
    main()