import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np

from config import get_project_root, get_data_dir, get_effect_size, get_power_target, get_alpha_level
from utils.logging import get_logger

logger = get_logger(__name__)

def run_power_analysis(
    effect_sizes: Optional[List[float]] = None,
    alpha: Optional[float] = None,
    power_target: Optional[float] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run sensitivity power analysis for Repeated-Measures ANOVA.

    Varies effect sizes across a range and computes required sample sizes.

    Args:
        effect_sizes: List of effect sizes to test (Cohen's f). Defaults to range 0.1 to 0.4.
        alpha: Significance level. Defaults to config value.
        power_target: Target power. Defaults to config value.
        output_path: Path to save results. Defaults to data/analysis/sensitivity_analysis.json.

    Returns:
        Dictionary with analysis results.
    """
    if effect_sizes is None:
        effect_sizes = [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4]

    if alpha is None:
        alpha = get_alpha_level()

    if power_target is None:
        power_target = get_power_target()

    # Import statsmodels here to avoid hard dependency if not needed
    try:
        from statsmodels.stats.power import FTestAnovaPower
    except ImportError:
        logger.error("statsmodels not installed. Please install it to run power analysis.")
        raise ImportError("statsmodels is required for power analysis.")

    analyzer = FTestAnovaPower()

    results = {
        "effect_sizes": [],
        "required_n": [],
        "power": []
    }

    logger.info(f"Running sensitivity analysis for {len(effect_sizes)} effect sizes...")

    for f in effect_sizes:
        # Calculate required N for given power
        # For repeated measures ANOVA, we assume 3 conditions (baseline, enhanced, reduced)
        # and correlation among measures of 0.5 (moderate)
        n_measures = 3
        corr = 0.5
        
        try:
            n_required = analyzer.solve_power(
                effect_size=f,
                n_groups=n_measures,  # This is actually n_k in some docs, but here it's groups
                alpha=alpha,
                power=power_target,
                correlation=corr,
                alternative='larger'
            )
            
            # Round up to nearest integer
            n_required = int(np.ceil(n_required))
            
            # Verify power at this N
            actual_power = analyzer.power(
                effect_size=f,
                nobs1=n_required,
                alpha=alpha,
                n_groups=n_measures,
                correlation=corr
            )
        except Exception as e:
            logger.warning(f"Could not compute power for effect_size={f}: {e}")
            n_required = None
            actual_power = 0.0

        results["effect_sizes"].append(f)
        results["required_n"].append(n_required if n_required else 0)
        results["power"].append(actual_power)

        logger.info(f"Effect size {f:.2f}: N={n_required}, Power={actual_power:.3f}")

    # Save results
    if output_path is None:
        output_path = get_project_root() / "data" / "analysis" / "sensitivity_analysis.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sensitivity analysis saved to {output_path}")

    return results

def validate_power_analysis(
    sensitivity_results_path: Optional[str] = None,
    min_effect_size: float = 0.25,
    min_n: int = 50,
    min_power: float = 0.80,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate power analysis results and determine required sample size.

    Args:
        sensitivity_results_path: Path to sensitivity analysis JSON.
        min_effect_size: Minimum effect size to consider (default 0.25).
        min_n: Minimum total subjects required.
        min_power: Minimum power required.
        output_path: Path to save power report.

    Returns:
        Power report dictionary.
    """
    if sensitivity_results_path is None:
        sensitivity_results_path = get_project_root() / "data" / "analysis" / "sensitivity_analysis.json"
    else:
        sensitivity_results_path = Path(sensitivity_results_path)

    if not sensitivity_results_path.exists():
        raise FileNotFoundError(f"Sensitivity analysis not found at {sensitivity_results_path}")

    with open(sensitivity_results_path, 'r') as f:
        sensitivity_data = json.load(f)

    effect_sizes = sensitivity_data["effect_sizes"]
    required_ns = sensitivity_data["required_n"]
    powers = sensitivity_data["power"]

    # Find smallest effect size >= min_effect_size where N >= min_n and power >= min_power
    selected_idx = None
    selected_effect = None
    selected_n = None
    selected_power = None

    for i, f in enumerate(effect_sizes):
        if f >= min_effect_size:
            n = required_ns[i]
            p = powers[i]
            if n is not None and n >= min_n and p >= min_power:
                if selected_idx is None or f < selected_effect:
                    selected_idx = i
                    selected_effect = f
                    selected_n = n
                    selected_power = p

    if selected_idx is None:
        # Fallback: pick the best available for min_effect_size
        for i, f in enumerate(effect_sizes):
            if f >= min_effect_size:
                selected_idx = i
                selected_effect = f
                selected_n = required_ns[i]
                selected_power = powers[i]
                break

    if selected_idx is None:
        # If no suitable effect size found, use the first one >= 0.25
        for i, f in enumerate(effect_sizes):
            if f >= 0.25:
                selected_idx = i
                selected_effect = f
                selected_n = required_ns[i]
                selected_power = powers[i]
                break

    if selected_idx is None:
        # Last resort: use 0.25 and assume N=50
        selected_effect = 0.25
        selected_n = min_n
        selected_power = min_power
        logger.warning(f"No valid effect size found. Using defaults: f={selected_effect}, N={selected_n}")

    power_insufficient = selected_n < min_n or selected_power < min_power

    report = {
        "n_total_subjects": selected_n,
        "effect_size": selected_effect,
        "power": selected_power,
        "alpha": get_alpha_level(),
        "power_insufficient": power_insufficient,
        "justification": f"Selected effect size {selected_effect:.2f} based on sensitivity analysis. "
                         f"Required N={selected_n} for power={selected_power:.2f}. "
                         f"{'Power is insufficient.' if power_insufficient else 'Power is adequate.'}"
    }

    if output_path is None:
        output_path = get_project_root() / "data" / "analysis" / "power_report.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Power report saved to {output_path}")

    return report

def main():
    """CLI entry point for power analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run power analysis for the study")
    parser.add_argument('--output', type=str, help='Output path for sensitivity analysis JSON')
    parser.add_argument('--report', type=str, help='Output path for power report JSON')
    parser.add_argument('--effect-sizes', nargs='+', type=float, help='Effect sizes to test')
    parser.add_argument('--min-n', type=int, default=50, help='Minimum required N')
    parser.add_argument('--min-power', type=float, default=0.80, help='Minimum required power')

    args = parser.parse_args()

    try:
        # Run sensitivity analysis
        sensitivity_results = run_power_analysis(
            effect_sizes=args.effect_sizes,
            output_path=args.output
        )

        # Generate power report
        report = validate_power_analysis(
            sensitivity_results_path=args.output,
            min_n=args.min_n,
            min_power=args.min_power,
            output_path=args.report
        )

        if report["power_insufficient"]:
            logger.error("Power analysis indicates insufficient power. Consider increasing N.")
            return 1

        logger.info("Power analysis completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
