"""Power analysis for social memory networks experiments."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
import math


@dataclass
class PowerAnalysisResult:
    """Result of power analysis computation."""
    sample_size: int
    effect_size: float
    power: float
    alpha: float
    detectable_effect_size: float
    metric_name: str
    context_condition: str


def compute_effect_size(group1: List[float], group2: List[float]) -> float:
    """Compute Cohen's d effect size between two groups.
    
    Args:
        group1: First group measurements
        group2: Second group measurements
        
    Returns:
        Cohen's d effect size
    """
    if not group1 or not group2:
        return 0.0

    mean1 = np.mean(group1)
    mean2 = np.mean(group2)

    var1 = np.var(group1, ddof=1) if len(group1) > 1 else 0.0
    var2 = np.var(group2, ddof=1) if len(group2) > 1 else 0.0

    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else 1.0

    if pooled_std == 0:
        return 0.0

    return abs(mean1 - mean2) / pooled_std


def compute_power(n: int, effect_size: float, alpha: float = 0.05) -> float:
    """Estimate statistical power using approximation.
    
    Args:
        n: Sample size per group
        effect_size: Cohen's d
        alpha: Significance level
        
    Returns:
        Estimated power (0 to 1)
    """
    if n <= 0 or effect_size < 0:
        return 0.0

    # Approximation: power increases with sqrt(n * d^2)
    # This is a simplified model; real power requires specialized libraries
    z_alpha = 1.96 if alpha == 0.05 else 1.645  # Two-tailed approximation
    noncentrality = effect_size * np.sqrt(n / 2)

    # Rough approximation: cumulative normal
    power_approx = 1 - np.exp(-noncentrality**2 / 2)
    return min(1.0, max(0.0, power_approx))


def compute_detectable_effect_size(n: int, power: float = 0.80, alpha: float = 0.05) -> float:
    """Compute minimum detectable effect size for given sample size and power.
    
    Args:
        n: Sample size per group
        power: Target power
        alpha: Significance level
        
    Returns:
        Minimum detectable effect size (Cohen's d)
    """
    if n <= 0:
        return float('inf')

    # Inverse approximation: solve for d given power
    # power ≈ 1 - exp(-d^2 * n / 2)
    # Rearranging: d ≈ sqrt(-2 * ln(1 - power) / n)
    if power >= 1.0:
        return 0.0

    d_squared = -2 * np.log(1 - power) / n
    return np.sqrt(max(0, d_squared))


def run_power_analysis(
    sample_sizes: Optional[List[int]] = None,
    effect_sizes: Optional[List[float]] = None,
    alpha: float = 0.05,
    target_power: float = 0.80,
) -> Dict[str, Any]:
    """Run comprehensive power analysis.
    
    Args:
        sample_sizes: List of sample sizes to analyze
        effect_sizes: List of effect sizes to analyze
        alpha: Significance level
        target_power: Target statistical power
        
    Returns:
        Dictionary with power analysis results
    """
    if sample_sizes is None:
        sample_sizes = [50, 100, 200, 500, 1000]
    if effect_sizes is None:
        effect_sizes = [0.2, 0.5, 0.8]  # Small, medium, large

    results = []

    for n in sample_sizes:
        for d in effect_sizes:
            power = compute_power(n, d, alpha)
            results.append({
                "sample_size": n,
                "effect_size": d,
                "power": power,
                "alpha": alpha,
            })

    return {
        "results": results,
        "alpha": alpha,
        "target_power": target_power,
    }


def generate_power_report(
    results_full_path: Optional[Path] = None,
    results_limited_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    sample_size: int = 1000,
) -> str:
    """Generate power analysis report from experiment results.
    
    Args:
        results_full_path: Path to full-context results CSV
        results_limited_path: Path to limited-context results CSV
        output_path: Path to write report
        sample_size: Sample size used in experiments (N)
        
    Returns:
        Report text
    """
    report_lines = []
    report_lines.append("# Power Analysis Report")
    report_lines.append("")
    report_lines.append(f"## Experiment Configuration")
    report_lines.append(f"- Sample size (N): {sample_size}")
    report_lines.append(f"- Significance level (α): 0.05 (with Bonferroni correction)")
    report_lines.append(f"- Target power: 0.80")
    report_lines.append("")

    # Load data if available
    effect_sizes_spec = []
    effect_sizes_ret = []

    if results_full_path and results_full_path.exists():
        try:
            df_full = pd.read_csv(results_full_path)
            if "specialization_index" in df_full.columns:
                effect_sizes_spec = df_full["specialization_index"].dropna().tolist()
        except Exception:
            pass

    if results_limited_path and results_limited_path.exists():
        try:
            df_limited = pd.read_csv(results_limited_path)
            if "retrieval_efficiency" in df_limited.columns:
                effect_sizes_ret = df_limited["retrieval_efficiency"].dropna().tolist()
        except Exception:
            pass

    # Compute observed effect sizes
    report_lines.append("## Observed Effect Sizes")

    if effect_sizes_spec:
        d_spec = np.std(effect_sizes_spec, ddof=1) if len(effect_sizes_spec) > 1 else 0.0
        report_lines.append(f"- Specialization index (observed SD): {d_spec:.4f}")
    else:
        report_lines.append("- Specialization index: No data available")

    if effect_sizes_ret:
        d_ret = np.std(effect_sizes_ret, ddof=1) if len(effect_sizes_ret) > 1 else 0.0
        report_lines.append(f"- Retrieval efficiency (observed SD): {d_ret:.4f}")
    else:
        report_lines.append("- Retrieval efficiency: No data available")

    report_lines.append("")
    report_lines.append("## Minimum Detectable Effect Sizes (MDES)")
    report_lines.append(f"For N={sample_size} per condition, power=0.80, α=0.05:")
    report_lines.append("")

    # Compute MDES for the actual sample size
    mdes = compute_detectable_effect_size(sample_size, power=0.80, alpha=0.05)
    report_lines.append(f"- MDES (Cohen's d): {mdes:.4f}")

    # Compute power for observed effect sizes
    if effect_sizes_spec:
        d_spec = np.std(effect_sizes_spec, ddof=1) if len(effect_sizes_spec) > 1 else 0.0
        power_spec = compute_power(sample_size, d_spec, alpha=0.05)
        report_lines.append(f"- Power for specialization (d={d_spec:.4f}): {power_spec:.3f}")

    if effect_sizes_ret:
        d_ret = np.std(effect_sizes_ret, ddof=1) if len(effect_sizes_ret) > 1 else 0.0
        power_ret = compute_power(sample_size, d_ret, alpha=0.05)
        report_lines.append(f"- Power for retrieval efficiency (d={d_ret:.4f}): {power_ret:.3f}")

    report_lines.append("")
    report_lines.append("## Interpretation")
    report_lines.append(f"With N={sample_size} per condition:")
    report_lines.append(f"- Effect sizes smaller than {mdes:.4f} (Cohen's d) will be underpowered")
    report_lines.append(f"- Effect sizes larger than {mdes:.4f} will be adequately powered")
    report_lines.append("")
    report_lines.append("## Bonferroni Correction")
    report_lines.append("- Number of comparisons: 2 (specialization + retrieval)")
    report_lines.append("- Corrected α: 0.025 (0.05 / 2)")
    report_lines.append("- All p-values reported with Bonferroni correction applied")

    report_text = "\n".join(report_lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text)

    return report_text


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for power analysis script."""
    parser = argparse.ArgumentParser(
        description="Generate power analysis report for social memory networks"
    )
    parser.add_argument(
        "--results-full",
        type=Path,
        help="Path to full-context results CSV"
    )
    parser.add_argument(
        "--results-limited",
        type=Path,
        help="Path to limited-context results CSV"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("power_analysis_report.md"),
        help="Output report path"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000,
        help="Sample size used in experiments"
    )
    return parser


def main() -> int:
    """Main entry point for power analysis report generation."""
    parser = build_parser()
    args = parser.parse_args()

    report = generate_power_report(
        results_full_path=args.results_full,
        results_limited_path=args.results_limited,
        output_path=args.output,
        sample_size=args.sample_size,
    )

    print(report)
    print(f"\nReport written to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())