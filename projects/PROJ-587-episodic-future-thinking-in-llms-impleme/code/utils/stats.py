"""
Statistical utilities for the Episodic Future Thinking project.

Implements power analysis and statistical testing utilities required for
experimental validation and pre-registration of study parameters.
"""
import json
import math
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Optional dependency: statsmodels for more advanced tests if needed later
# Currently using standard math for power analysis calculation
try:
    from scipy import stats
    import numpy as np
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Fallback math implementations will be used if scipy is missing
    pass

def _norm_ppf(p: float) -> float:
    """
    Approximate inverse of the standard normal CDF (percent point function).
    Used for power analysis calculations when scipy is not available.
    Implementation based on Abramowitz and Stegun approximation.
    """
    if p <= 0 or p >= 1:
        raise ValueError("p must be between 0 and 1")
    if p == 0.5:
        return 0.0
    
    # Constants for approximation
    a1 = -3.969683028665376e+01
    a2 = 2.209460984245205e+02
    a3 = -2.759285104469687e+02
    a4 = 1.383577518672690e+02
    a5 = -3.066479806614716e+01
    a6 = 2.506628277459239e+00

    b1 = -5.447609879822406e+01
    b2 = 1.615858368580409e+02
    b3 = -1.556989798598866e+02
    b4 = 6.680131188771972e+01
    b5 = -1.328068155288572e+01

    c1 = -7.784894002430293e-03
    c2 = -3.223964580411365e-01
    c3 = -2.400758277161838e+00
    c4 = -2.549732539343734e+00
    c5 = 4.374664141464968e+00
    c6 = 2.938163982698783e+00

    d1 = 7.784695709041462e-03
    d2 = 3.224671290700398e-01
    d3 = 2.445134137142996e+00
    d4 = 3.754408661907416e+00

    p_low = 0.02425
    p_high = 1 - p_low

    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) / ((((d1*q+d2)*q+d3)*q+d4)*q+1)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a1*r+a2)*r+a3)*r+a4)*r+a5)*r+a6)*q / (((((b1*r+b2)*r+b3)*r+b4)*r+b5)*r+1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c1*q+c2)*q+c3)*q+c4)*q+c5)*q+c6) / ((((d1*q+d2)*q+d3)*q+d4)*q+1)

def calculate_power_analysis(
    n_per_group: int,
    effect_size: float,
    alpha: float = 0.05,
    two_tailed: bool = True
) -> Dict[str, float]:
    """
    Calculate statistical power for a two-sample t-test.
    
    Args:
        n_per_group: Number of samples in each group
        effect_size: Cohen's d effect size
        alpha: Significance level (default 0.05)
        two_tailed: Whether to use two-tailed test (default True)
        
    Returns:
        Dictionary containing power, critical values, and test parameters
    """
    if n_per_group <= 0:
        raise ValueError("n_per_group must be positive")
    if effect_size == 0:
        return {
            "power": 0.0 if two_tailed else 0.5,
            "effect_size": effect_size,
            "n_per_group": n_per_group,
            "alpha": alpha,
            "two_tailed": two_tailed
        }
        
    # Degrees of freedom for two-sample t-test
    df = 2 * n_per_group - 2
    
    # Critical t-value
    if two_tailed:
        alpha_adj = alpha / 2
    else:
        alpha_adj = alpha
        
    if SCIPY_AVAILABLE:
        critical_t = stats.t.ppf(1 - alpha_adj, df)
    else:
        # Approximation using normal distribution for large df
        critical_t = _norm_ppf(1 - alpha_adj)
    
    # Non-centrality parameter
    ncp = effect_size * math.sqrt(n_per_group / 2)
    
    # Power calculation
    if SCIPY_AVAILABLE:
        # Power = P(T > critical_t | non-central t distribution)
        power = 1 - stats.nct.cdf(critical_t, df, ncp)
        if two_tailed:
            # Add lower tail probability
            power += stats.nct.cdf(-critical_t, df, ncp)
    else:
        # Approximation using normal distribution
        # Power ≈ Φ(ncp - z_crit) for one-tailed
        z_crit = critical_t
        if two_tailed:
            # For two-tailed, we consider both tails
            # Approximate as one-tailed with adjusted alpha
            z_crit = _norm_ppf(1 - alpha / 2)
            power = 1 - _norm_ppf(z_crit - ncp) + _norm_ppf(-z_crit - ncp)
        else:
            power = 1 - _norm_ppf(z_crit - ncp)
        
        # Clamp power to [0, 1]
        power = max(0.0, min(1.0, power))
    
    return {
        "power": float(power),
        "effect_size": float(effect_size),
        "n_per_group": n_per_group,
        "alpha": float(alpha),
        "two_tailed": two_tailed,
        "degrees_of_freedom": df,
        "critical_t_value": float(critical_t),
        "non_central_parameter": float(ncp)
    }

def run_power_analysis(
    output_path: Optional[str] = None,
    n_variants: int = 10,
    target_power: float = 0.80,
    target_effect_size: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a pre-registered power analysis report.
    
    This function calculates the required sample size and power for the
    planned experiments, ensuring statistical validity before data collection.
    
    Args:
        output_path: Path to save the JSON report. If None, returns dict only.
        n_variants: Number of experimental variants (default 10)
        target_power: Target statistical power (default 0.80)
        target_effect_size: Expected effect size (Cohen's d, default 0.8)
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary containing the complete power analysis report
    """
    # Calculate required sample size per group for target power
    # We'll iterate to find the minimum n that achieves target_power
    min_n = 2
    max_n = 1000
    required_n_per_group = max_n
    
    for n in range(min_n, max_n + 1):
        result = calculate_power_analysis(
            n_per_group=n,
            effect_size=target_effect_size,
            alpha=alpha,
            two_tailed=True
        )
        if result["power"] >= target_power:
            required_n_per_group = n
            break
    
    # Calculate total sample size
    total_sample_size = required_n_per_group * 2  # Two groups: control vs experimental
    
    # Build report
    report = {
        "report_metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "report_type": "power_analysis",
            "version": "1.0",
            "constitution_principle": "VII",
            "description": "Pre-registered power analysis for Episodic Future Thinking experiments"
        },
        "experimental_design": {
            "n_variants": n_variants,
            "test_type": "two-sample_t_test",
            "two_tailed": True,
            "alpha": alpha,
            "target_power": target_power,
            "expected_effect_size": target_effect_size
        },
        "sample_size_requirements": {
            "n_per_group": required_n_per_group,
            "total_sample_size": total_sample_size,
            "groups": ["control", "experimental"],
            "note": "Sample size calculated for the primary comparison. Additional variants will require adjustment."
        },
        "power_calculation": calculate_power_analysis(
            n_per_group=required_n_per_group,
            effect_size=target_effect_size,
            alpha=alpha,
            two_tailed=True
        ),
        "power_analysis_by_variant": [],
        "recommendations": [
            f"Recruit at least {total_sample_size} total samples across all variants",
            f"Each variant should have {required_n_per_group} samples per group",
            "Ensure random assignment to control and experimental conditions",
            "Pre-register analysis plan before data collection",
            "Consider Bonferroni correction for multiple comparisons across variants"
        ]
    }
    
    # Add variant-specific analysis
    for i in range(1, n_variants + 1):
        variant_analysis = {
            "variant_id": i,
            "n_per_group": required_n_per_group,
            "total_for_variant": required_n_per_group * 2,
            "achieved_power": calculate_power_analysis(
                n_per_group=required_n_per_group,
                effect_size=target_effect_size,
                alpha=alpha,
                two_tailed=True
            )["power"]
        }
        report["power_analysis_by_variant"].append(variant_analysis)
    
    # Save to file if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
    
    return report

def main():
    """Main entry point for running power analysis."""
    import os
    
    # Determine output path
    project_root = Path(__file__).parent.parent
    output_path = project_root / "data" / "reports" / "power_analysis_report.json"
    
    print(f"Generating power analysis report...")
    print(f"Output path: {output_path}")
    
    # Run analysis
    report = run_power_analysis(
        output_path=str(output_path),
        n_variants=10,
        target_power=0.80,
        target_effect_size=0.8,
        alpha=0.05
    )
    
    print(f"Power analysis complete!")
    print(f"Required samples per group: {report['sample_size_requirements']['n_per_group']}")
    print(f"Total required samples: {report['sample_size_requirements']['total_sample_size']}")
    print(f"Achieved power: {report['power_calculation']['power']:.4f}")
    print(f"Report saved to: {output_path}")
    
    return report

if __name__ == "__main__":
    main()
