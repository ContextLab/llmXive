"""
Power Analysis Module for Repeated-Measures ANOVA.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np
from statsmodels.stats.power import FTestAnovaPower
from statsmodels.stats.anova import AnovaRM

from config import get_project_root, get_data_dir, get_effect_size, get_alpha_level, get_power_target
from analysis.stats import calculate_anova_power, save_power_analysis

logger = logging.getLogger(__name__)

def run_power_analysis(
    effect_size: Optional[float] = None,
    alpha: Optional[float] = None,
    power_target: Optional[float] = None,
    n_measurements: int = 3,  # Baseline, Enhanced, Reduced
    sensitivity_analysis_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform power analysis for Repeated-Measures ANOVA.

    Args:
        effect_size: Cohen's f effect size. If None, loads from sensitivity analysis.
        alpha: Significance level.
        power_target: Target power (1 - beta).
        n_measurements: Number of repeated measures (conditions).
        sensitivity_analysis_path: Path to sensitivity analysis JSON.

    Returns:
        Dictionary with power analysis results.
    """
    # Load sensitivity analysis if effect_size not provided
    if effect_size is None and sensitivity_analysis_path:
        sens_path = Path(sensitivity_analysis_path)
        if sens_path.exists():
            with open(sens_path, 'r') as f:
                sens_data = json.load(f)
            # Select effect_size based on logic: min required_n >= 50
            required_n_list = sens_data.get("required_n", [])
            effect_sizes = sens_data.get("effect_sizes", [])
            
            # Find minimum n that satisfies n >= 50
            valid_indices = [i for i, n in enumerate(required_n_list) if n >= 50]
            if valid_indices:
                min_idx = min(valid_indices, key=lambda i: required_n_list[i])
                effect_size = effect_sizes[min_idx]
                logger.info(f"Selected effect_size {effect_size} from sensitivity analysis (N={required_n_list[min_idx]})")
            else:
                # Use largest N available
                max_idx = np.argmax(required_n_list)
                effect_size = effect_sizes[max_idx]
                logger.warning(f"No N >= 50 found. Using effect_size {effect_size} (N={required_n_list[max_idx]})")
        else:
            logger.warning("Sensitivity analysis file not found. Using default effect size.")
            effect_size = get_effect_size()

    if alpha is None:
        alpha = get_alpha_level()
    if power_target is None:
        power_target = get_power_target()

    # Use FTestAnovaPower for repeated measures approximation
    # Note: statsmodels doesn't have a dedicated repeated-measures power class,
    # so we use F-test as approximation for within-subjects design
    power_analysis = FTestAnovaPower()

    # Calculate required sample size
    n_subjects = power_analysis.solve_power(
        effect_size=effect_size,
        alpha=alpha,
        power=power_target,
        n_groups=n_measurements,  # Number of conditions
        alternative='larger'
    )

    n_subjects = int(np.ceil(n_subjects))

    # Calculate achieved power for this N
    achieved_power = power_analysis.power(
        effect_size=effect_size,
        alpha=alpha,
        nobs1=n_subjects / n_measurements,  # Per group
        n_groups=n_measurements
    )

    # Determine if power is sufficient (N >= 50)
    power_insufficient = n_subjects < 50

    result = {
        "n_total_subjects": n_subjects,
        "effect_size": effect_size,
        "power": float(achieved_power),
        "alpha": alpha,
        "power_insufficient": power_insufficient,
        "justification": f"Calculated for Repeated-Measures ANOVA with {n_measurements} conditions. "
                        f"Effect size {effect_size} selected from sensitivity analysis. "
                        f"Target power: {power_target}, Alpha: {alpha}."
    }

    return result

def validate_power_analysis(power_report_path: str) -> bool:
    """
    Validate that power analysis meets criteria.

    Args:
        power_report_path: Path to the power report JSON.

    Returns:
        True if validation passes, False otherwise.
    """
    path = Path(power_report_path)
    if not path.exists():
        logger.error(f"Power report not found: {power_report_path}")
        return False

    try:
        with open(path, 'r') as f:
            report = json.load(f)

        if report.get("power_insufficient", True):
            logger.error("Power analysis failed: power_insufficient is true")
            return False

        n_subjects = report.get("n_total_subjects", 0)
        if n_subjects < 50:
            logger.error(f"Power analysis failed: N={n_subjects} < 50")
            return False

        logger.info("Power analysis validation passed")
        return True

    except Exception as e:
        logger.error(f"Failed to validate power analysis: {e}")
        return False

def main() -> None:
    """Main entry point for power analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Run power analysis for repeated-measures ANOVA")
    parser.add_argument("--sensitivity-path", default="data/analysis/sensitivity_analysis.json",
                      help="Path to sensitivity analysis JSON")
    parser.add_argument("--output-path", default="data/analysis/power_report.json",
                      help="Path to output power report")
    parser.add_argument("--validate", action="store_true", help="Run validation after calculation")
    args = parser.parse_args()

    # Run power analysis
    result = run_power_analysis(sensitivity_analysis_path=args.sensitivity_path)

    # Save result
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Power report saved to {output_path}")
    logger.info(f"N subjects required: {result['n_total_subjects']}")
    logger.info(f"Power sufficient: {not result['power_insufficient']}")

    # Validate if requested
    if args.validate:
        if not validate_power_analysis(args.output_path):
            logger.error("Power analysis validation failed. Pipeline blocked.")
            sys.exit(1)
        else:
            # Write gate passed file
            gate_path = Path("data/analysis/power_gate_passed.txt")
            gate_path.parent.mkdir(parents=True, exist_ok=True)
            gate_path.write_text("Power analysis validation passed.\n")
            logger.info("Power gate passed. Pipeline can proceed.")

if __name__ == "__main__":
    main()
