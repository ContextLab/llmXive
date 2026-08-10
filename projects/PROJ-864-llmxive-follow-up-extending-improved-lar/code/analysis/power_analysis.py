"""
Power analysis module for User Story 3.

Implements T034: A priori power analysis for 1M token / 5-seed regime.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from statsmodels.stats.power import FTestAnovaPower, TTestIndPower

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, info, error, warning
from utils.config import get_artifacts_dir

logger = get_logger(__name__)


def compute_effect_size(
    group1_data: np.ndarray,
    group2_data: np.ndarray
) -> float:
    """
    Compute Cohen's d effect size between two groups.
    
    Args:
        group1_data: First group data
        group2_data: Second group data
        
    Returns:
        Cohen's d effect size
    """
    mean1 = np.mean(group1_data)
    mean2 = np.mean(group2_data)
    std1 = np.std(group1_data, ddof=1)
    std2 = np.std(group2_data, ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(group1_data), len(group2_data)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return abs(mean1 - mean2) / pooled_std


def perform_power_analysis(
    effect_size: Optional[float] = None,
    n_groups: int = 2,
    n_per_group: int = 5,
    alpha: float = 0.05,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform a priori power analysis for the experimental design.
    
    Implements T034: Verify power >= 0.8 for 1M token / 5-seed regime.
    
    Args:
        effect_size: Expected effect size (Cohen's d). If None, uses typical values.
        n_groups: Number of groups (model types)
        n_per_group: Number of samples per group (seeds)
        alpha: Significance level
        output_path: Path to save results
        
    Returns:
        Dictionary with power analysis results
    """
    logger.info("Performing a priori power analysis")
    
    # Default effect size based on typical ML experiments
    if effect_size is None:
        # Assume a moderate effect size for overfitting gap differences
        effect_size = 0.8  # Cohen's d = 0.8 is considered "large"
    
    total_samples = n_groups * n_per_group
    
    # Power analysis for ANOVA (comparing multiple groups)
    power_analysis = FTestAnovaPower()
    
    # Calculate power for ANOVA
    # f = effect_size / sqrt(k) where k is number of groups
    # For 2 groups, f ≈ effect_size / sqrt(2)
    f_effect = effect_size / np.sqrt(n_groups)
    
    power = power_analysis.solve_power(
        effect_size=f_effect,
        nobs1=total_samples / n_groups,  # samples per group
        alpha=alpha,
        power=None,  # We're solving for power
        ratio=1.0,  # Equal group sizes
        alternative='two-sided'
    )
    
    # Also compute for t-test (pairwise comparison)
    t_test_power = TTestIndPower()
    power_t = t_test_power.solve_power(
        effect_size=effect_size,
        n1=total_samples / n_groups,
        alpha=alpha,
        power=None,
        ratio=1.0
    )
    
    # Determine if power meets threshold
    power_threshold = 0.8
    power_met = power >= power_threshold if power else False
    
    results = {
        "method": "A priori power analysis",
        "test_type": "ANOVA with pairwise t-test",
        "design": {
            "n_groups": n_groups,
            "n_per_group": n_per_group,
            "total_samples": total_samples,
            "effect_size_assumed": effect_size,
            "alpha": alpha
        },
        "results": {
            "anova_power": float(power) if power else None,
            "t_test_power": float(power_t) if power_t else None,
            "power_threshold": power_threshold,
            "power_met": power_met,
            "required_samples_for_80pct_power": power_analysis.solve_power(
                effect_size=f_effect,
                nobs1=None,
                alpha=alpha,
                power=0.8,
                ratio=1.0
            ) if power else None
        },
        "interpretation": {
            "sufficient_power": power_met,
            "recommendation": "Proceed with experiment" if power_met else "Consider increasing sample size or effect size",
            "notes": [
                f"Assumed effect size (Cohen's d): {effect_size}",
                f"Current design: {n_groups} groups x {n_per_group} seeds = {total_samples} total samples",
                f"Power for ANOVA: {power:.3f} (threshold: {power_threshold})",
                f"Power for t-test: {power_t:.3f}"
            ]
        }
    }
    
    # Save results
    if output_path is None:
        output_path = str(get_artifacts_dir() / "power_analysis_results.json")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    info(f"Power analysis results saved to {output_path}")
    info(f"Power met threshold (>=0.8): {power_met}")
    info(f"ANOVA power: {power:.3f if power else 'N/A'}")
    
    return results


def main():
    """Main entry point for power analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Perform a priori power analysis")
    parser.add_argument("--effect-size", type=float, help="Expected effect size (Cohen's d)")
    parser.add_argument("--n-groups", type=int, default=2, help="Number of groups")
    parser.add_argument("--n-per-group", type=int, default=5, help="Samples per group")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    parser.add_argument("--output", type=str, help="Path to output JSON file")
    
    args = parser.parse_args()
    
    try:
        results = perform_power_analysis(
            effect_size=args.effect_size,
            n_groups=args.n_groups,
            n_per_group=args.n_per_group,
            alpha=args.alpha,
            output_path=args.output
        )
        
        info("Power analysis completed")
        info(f"Power threshold met: {results['interpretation']['sufficient_power']}")
        
    except Exception as e:
        error(f"Power analysis failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
