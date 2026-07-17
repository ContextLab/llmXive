"""
Power Analysis and Minimum Detectable Effect Size (MDES) Calculation.

This module implements the statistical power analysis required to determine
if the study (n=50) is sufficiently powered to detect subtle biases.
It calculates the Minimum Detectable Effect Size (MDES) and generates a
formal report documenting limitations.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
from scipy import stats

from code.config import get_project_root

# Setup logging
logger = logging.getLogger(__name__)

def calculate_mdes(
    n: int,
    alpha: float = 0.05,
    power: float = 0.80,
    two_tailed: bool = True
) -> float:
    """
    Calculate the Minimum Detectable Effect Size (Cohen's d) given sample size,
    alpha, and desired power.

    Uses the non-central t-distribution approximation for two-sample t-test.
    For large N, the non-centrality parameter (ncp) approximates d * sqrt(n/2).
    However, for n=50, we use the standard approximation:
    ncp = t_crit + t_beta (where t_beta is the critical value for power)

    Args:
        n: Total sample size (assumed equal groups, so n1=n2=n/2)
        alpha: Significance level (Type I error rate)
        power: Desired statistical power (1 - Type II error rate)
        two_tailed: Whether the test is two-tailed

    Returns:
        float: Minimum Detectable Effect Size (Cohen's d)
    """
    if n < 4:
        raise ValueError("Sample size must be at least 4 for valid t-test approximation.")

    # Degrees of freedom for two-sample t-test (assuming equal variance, equal n)
    # If n is total, then n_per_group = n/2. df = n_per_group + n_per_group - 2 = n - 2.
    df = n - 2
    n_per_group = n / 2.0

    # Critical t-value for alpha
    if two_tailed:
        t_crit = stats.t.ppf(1 - alpha / 2, df)
    else:
        t_crit = stats.t.ppf(1 - alpha, df)

    # Critical t-value for power (beta)
    # We need the non-centrality parameter (ncp) such that P(t > t_crit | ncp) = power
    # Approximation: ncp ≈ t_crit + t_beta
    # t_beta is the quantile for (1 - power)
    t_beta = stats.t.ppf(power, df)

    # Non-centrality parameter required
    ncp_required = t_crit + t_beta

    # Relationship between ncp and Cohen's d:
    # ncp = d * sqrt(n1 * n2 / (n1 + n2)) = d * sqrt((n/2)*(n/2) / n) = d * sqrt(n/4) = d * sqrt(n)/2
    # Therefore: d = ncp * 2 / sqrt(n)
    mdes = ncp_required * 2.0 / np.sqrt(n)

    return mdes

def calculate_power(
    n: int,
    effect_size: float,
    alpha: float = 0.05,
    two_tailed: bool = True
) -> float:
    """
    Calculate statistical power given sample size and effect size.

    Args:
        n: Total sample size
        effect_size: Cohen's d
        alpha: Significance level
        two_tailed: Whether the test is two-tailed

    Returns:
        float: Statistical power (0.0 to 1.0)
    """
    if n < 4:
        return 0.0

    df = n - 2
    n_per_group = n / 2.0

    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n_per_group / 2.0) # sqrt(n1*n2/(n1+n2)) -> sqrt(n/4) = sqrt(n)/2
    # Wait, standard formula: ncp = d * sqrt( n1*n2 / (n1+n2) )
    # If n1=n2=n/2: ncp = d * sqrt( (n^2/4) / n ) = d * sqrt(n/4) = d * sqrt(n)/2
    ncp = effect_size * np.sqrt(n) / 2.0

    if two_tailed:
        t_crit = stats.t.ppf(1 - alpha / 2, df)
        # Power is P(|T| > t_crit | ncp)
        # P(T < -t_crit) + P(T > t_crit)
        # Using survival function for the upper tail and cdf for lower
        # Note: scipy.stats.nct.cdf(x, df, ncp)
        p_upper = 1.0 - stats.nct.cdf(t_crit, df, ncp)
        p_lower = stats.nct.cdf(-t_crit, df, ncp)
        power = p_upper + p_lower
    else:
        t_crit = stats.t.ppf(1 - alpha, df)
        power = 1.0 - stats.nct.cdf(t_crit, df, ncp)

    return max(0.0, min(1.0, power))

def load_observed_effect_size(
    aggregated_path: Optional[Path] = None
) -> Optional[float]:
    """
    Attempt to load the observed effect size from the aggregated bias data.
    If the file is missing, returns None.

    Args:
        aggregated_path: Path to aggregated_bias.csv

    Returns:
        float or None
    """
    if aggregated_path is None:
        root = get_project_root()
        aggregated_path = root / "data" / "processed" / "aggregated_bias.csv"

    if not aggregated_path.exists():
        logger.warning(f"Aggregated bias file not found at {aggregated_path}. Cannot calculate observed effect size.")
        return None

    try:
        # We expect a column 'slope' or 'effect_size' in the stats files,
        # but for a simple heuristic, we can look at the mean bias deviation
        # relative to the standard deviation of the noise.
        # However, the most direct way is to read the regression slope from the stats file
        # if it represents the effect size.
        # For this task, we will assume the 'slope' from the regression stats represents the effect magnitude.
        # If that's not available, we might need to compute it from raw data.
        # Let's try to read the noise_stats.csv and saturation_stats.csv if available.
        # For now, we return None if we can't find a direct metric, as the spec asks to
        # "use observed effect size" which implies it was calculated previously.
        # We will return None to indicate we cannot auto-load it without a specific schema agreement.
        # In a real scenario, we would parse the 'slope' from data/processed/noise_stats.csv.
        pass
    except Exception as e:
        logger.error(f"Failed to load observed effect size: {e}")

    return None

def generate_power_report(
    n: int = 50,
    alpha: float = 0.05,
    power_target: float = 0.80,
    observed_effect_size: Optional[float] = None,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive power analysis report.

    Args:
        n: Sample size used in the study
        alpha: Significance level
        power_target: Target power (usually 0.80)
        observed_effect_size: The effect size observed in the data (if known)
        output_path: Path to write the markdown report

    Returns:
        Dictionary containing the report data
    """
    if output_path is None:
        root = get_project_root()
        output_path = root / "data" / "validation" / "power_analysis_report.md"

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Calculate MDES
    mdes = calculate_mdes(n, alpha, power_target)

    # Calculate actual power for the observed effect (if available)
    actual_power = None
    power_status = "Unknown"
    if observed_effect_size is not None:
        actual_power = calculate_power(n, observed_effect_size, alpha)
        if actual_power >= power_target:
            power_status = "Sufficient"
        else:
            power_status = "Underpowered"

    # Determine limitations
    limitations = []
    if mdes > 0.05:
        limitations.append(
            f"The study is underpowered to detect subtle biases (< 0.05). "
            f"Minimum Detectable Effect Size (MDES) is {mdes:.4f}."
        )
    if observed_effect_size is not None and actual_power is not None and actual_power < power_target:
        limitations.append(
            f"With the observed effect size of {observed_effect_size:.4f}, "
            f"the achieved power is only {actual_power:.2%}, which is below the target {power_target:.0%}."
        )

    report_data = {
        "sample_size": n,
        "alpha": alpha,
        "target_power": power_target,
        "minimum_detectable_effect_size": mdes,
        "observed_effect_size": observed_effect_size,
        "achieved_power": actual_power,
        "power_status": power_status,
        "limitations": limitations,
        "conclusion": "The study is underpowered for subtle biases." if mdes > 0.05 else "The study is sufficiently powered for moderate to large effects."
    }

    # Generate Markdown content
    md_lines = [
        "# Power Analysis Report",
        "",
        "## Study Parameters",
        f"- **Sample Size (n):** {n}",
        f"- **Significance Level (alpha):** {alpha}",
        f"- **Target Power:** {power_target:.0%}",
        "",
        "## Results",
        f"- **Minimum Detectable Effect Size (MDES):** {mdes:.4f}",
        f"- **Observed Effect Size:** {observed_effect_size if observed_effect_size is not None else 'Not Available'}",
        f"- **Achieved Power:** {actual_power:.2%}" if actual_power else "- **Achieved Power:** N/A",
        "",
        "## Limitations",
    ]

    if limitations:
        for lim in limitations:
            md_lines.append(f"- {lim}")
    else:
        md_lines.append("- No significant power limitations detected for the target effect size.")

    md_lines.extend([
        "",
        "## Conclusion",
        f"{report_data['conclusion']}",
        "",
        "### Interpretation",
        f"The Minimum Detectable Effect Size (MDES) of {mdes:.4f} indicates that with a sample size of {n},",
        f"the study can only reliably detect effect sizes larger than {mdes:.4f}.",
        "Biases smaller than this threshold may not be statistically distinguishable from zero.",
    ])

    if mdes > 0.05:
        md_lines.append("")
        md_lines.append(f"**CRITICAL WARNING:** The study is underpowered for detecting subtle biases (< 0.05).")
        md_lines.append(f"Any non-significant results for effects smaller than {mdes:.4f} should be interpreted with caution.")

    # Write file
    md_content = "\n".join(md_lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    logger.info(f"Power analysis report written to {output_path}")

    return report_data

def main():
    """
    Main entry point for running the power analysis.
    """
    logging.basicConfig(level=logging.INFO)
    root = get_project_root()

    # Path to aggregated bias data (optional, for observed effect size)
    aggregated_path = root / "data" / "processed" / "aggregated_bias.csv"

    observed_es = None
    if aggregated_path.exists():
        # Attempt to infer effect size from the slope of the regression
        # This is a heuristic. In a full implementation, we would calculate Cohen's d
        # from the raw bias distributions.
        try:
            import pandas as pd
            df = pd.read_csv(aggregated_path)
            # If 'slope' column exists, use it as a proxy for effect magnitude
            if 'slope' in df.columns:
                # Take the average absolute slope as a rough estimate of effect size
                # Note: This is a simplification. Real Cohen's d requires std dev of the bias.
                avg_slope = df['slope'].abs().mean()
                # We need a std dev to convert slope to Cohen's d.
                # Assuming the bias std dev is roughly 1 (normalized) for this heuristic,
                # or we just report the slope as the effect metric if d is not calculable.
                # For this task, we will calculate d if we can estimate sigma.
                # If we can't, we set observed_es to None and report MDES only.
                # Let's try to find a column with 'std' or 'bias_std'
                if 'bias_std' in df.columns:
                    sigma = df['bias_std'].mean()
                    if sigma > 0:
                        observed_es = avg_slope / sigma
                    else:
                        observed_es = None
                else:
                    observed_es = None # Cannot calculate d without sigma
        except Exception as e:
            logger.warning(f"Could not calculate observed effect size from {aggregated_path}: {e}")
            observed_es = None

    report = generate_power_report(
        n=50,
        observed_effect_size=observed_es,
        output_path=root / "data" / "validation" / "power_analysis_report.md"
    )

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
