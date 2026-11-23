"""
Power Analysis & Gap Resolution for Phenomenological AI Study.

This script calculates the sample size gap between the Spec requirement (N=80 per prompt)
and the CI hardware limits (N=20 per prompt). It generates a report defining the
'Pilot Mode' vs 'Full Study' execution paths.

Execution: python code/generation/power_analysis.py
Output: data/raw/power_gap_report.md
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import get_config

def calculate_power_gap(
    spec_n: int = 80,
    ci_n: int = 20,
    num_prompts: int = 4,
    num_strategies: int = 4
) -> Dict[str, Any]:
    """
    Calculate the gap between Spec requirements and CI limitations.

    Args:
        spec_n: Required samples per prompt per strategy (from Spec)
        ci_n: Maximum feasible samples per prompt per strategy on CI
        num_prompts: Number of distinct prompt templates
        num_strategies: Number of prompting strategies (Direct, Hypothetical, etc.)

    Returns:
        Dictionary containing gap analysis metrics.
    """
    total_spec = spec_n * num_prompts * num_strategies
    total_ci = ci_n * num_prompts * num_strategies
    gap_per_condition = spec_n - ci_n
    total_gap = total_spec - total_ci
    coverage_pct = (total_ci / total_spec) * 100

    return {
        "spec_total": total_spec,
        "ci_total": total_ci,
        "gap_per_condition": gap_per_condition,
        "total_gap": total_gap,
        "coverage_pct": coverage_pct,
        "spec_n": spec_n,
        "ci_n": ci_n,
        "num_prompts": num_prompts,
        "num_strategies": num_strategies
    }

def generate_report(metrics: Dict[str, Any]) -> str:
    """
    Generate a Markdown report describing the power gap and execution paths.

    Args:
        metrics: Dictionary from calculate_power_gap

    Returns:
        Markdown formatted string.
    """
    report_lines = [
        "# Power Analysis & Gap Resolution Report",
        "",
        "## Executive Summary",
        f"This report analyzes the sample size gap between the Spec requirement (N={metrics['spec_n']} per prompt) "
        f"and the CI hardware limitations (N={metrics['ci_n']} per prompt).",
        "",
        "## Calculated Metrics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Spec Total Samples (Full Study) | {metrics['spec_total']:,} |",
        f"| CI Feasible Samples (Pilot Mode) | {metrics['ci_total']:,} |",
        f"| Gap Per Condition (Prompt × Strategy) | {metrics['gap_per_condition']:,} |",
        f"| Total Sample Gap | {metrics['total_gap']:,} |",
        f"| CI Coverage of Spec | {metrics['coverage_pct']:.1f}% |",
        "",
        "## Execution Paths",
        "",
        "### 1. Pilot Mode (CI Path)",
        "- **Target**: `data/raw/` (TinyLlama, CPU)",
        f"- **Volume**: {metrics['ci_n']} samples per prompt per strategy.",
        f"- **Total**: {metrics['ci_total']} samples.",
        "- **Purpose**: Automated validation, schema checks, and preliminary metric calculation.",
        "- **Limitation**: Statistical power is reduced; results are indicative, not definitive.",
        "",
        "### 2. Full Study (GPU Offload / Local)",
        "- **Target**: `data/raw/` (Mistral-7B / Llama-7B, GPU)",
        f"- **Volume**: {metrics['spec_n']} samples per prompt per strategy.",
        f"- **Total**: {metrics['spec_total']} samples.",
        "- **Purpose**: Final statistical analysis, inter-rater reliability, and publication-grade results.",
        "- **Constraint**: Requires GPU resources (Kaggle free-tier or local hardware >16GB RAM).",
        "",
        "## Recommendations",
        "",
        f"1. **Default CI Execution**: Run with N={metrics['ci_n']} to ensure rapid feedback loops.",
        f"2. **Trigger Full Study**: When N={metrics['spec_n']} is required for FR-001 compliance, "
        "switch to the GPU-offloaded runner (`runner_gpu.py`).",
        f"3. **Gap Mitigation**: The {metrics['total_gap']:,} sample gap represents a {100 - metrics['coverage_pct']:.1f}% reduction in statistical power. "
        "Interpret CI results with caution and reserve final claims for the Full Study path.",
        "",
        "## Methodology",
        "",
        "The gap is calculated as: `Gap = (Spec_N - CI_N) × Num_Prompts × Num_Strategies`.",
        "Coverage is calculated as: `(CI_Total / Spec_Total) × 100`.",
        "",
        f"Generated at: {__import__('datetime').datetime.utcnow().isoformat()}Z"
    ]
    return "\n".join(report_lines)

def main():
    """Main entry point."""
    print("Starting Power Analysis & Gap Resolution...")

    # Ensure output directory exists
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "power_gap_report.md"

    # Configuration parameters (derived from Spec and Plan)
    # Spec FR-001/Plan: N=80 per prompt
    # CI Constraint: N=20 per prompt (TinyLlama CPU limit)
    config = get_config()
    
    # Hardcoded logic for this specific analysis based on T009d requirements
    spec_n = 80
    ci_n = 20
    num_prompts = 4  # As per T009 description (4 strategies × 4 prompts = 1600 total for full)
    num_strategies = 4

    metrics = calculate_power_gap(
        spec_n=spec_n,
        ci_n=ci_n,
        num_prompts=num_prompts,
        num_strategies=num_strategies
    )

    report_content = generate_report(metrics)

    # Write the report to disk
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Power analysis complete. Report written to: {output_path}")
    print(f"  - Spec Total: {metrics['spec_total']}")
    print(f"  - CI Total: {metrics['ci_total']}")
    print(f"  - Gap: {metrics['total_gap']}")

if __name__ == "__main__":
    main()
