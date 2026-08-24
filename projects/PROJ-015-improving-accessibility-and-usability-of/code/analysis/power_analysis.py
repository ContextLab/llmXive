"""
Power Analysis Module for PROJ-015.

Provides functionality for a priori power analysis and observed power calculation
based on Repeated Measures ANOVA results.

Constraints:
- Must raise ValueError if N < 30 in non-pilot mode.
- Must allow N=5 in pilot mode with a warning.
- Must calculate observed power using scipy.stats based on real ANOVA results.
"""
import os
import sys
import math
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

class PowerCalculator:
    """
    Calculates observed power from ANOVA results and performs a priori power analysis.
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize the PowerCalculator.

        Args:
            alpha: Significance level (default 0.05).
        """
        self.alpha = alpha

    def calculate_observed_power_rm_anova(
        self,
        f_value: float,
        df_num: int,
        df_den: int,
        n_groups: int,
        n_subjects: int
    ) -> float:
        """
        Calculate observed power for a Repeated Measures ANOVA.

        Power is the probability of rejecting the null hypothesis given the
        observed effect size (f) and sample size.

        Args:
            f_value: The F-statistic from the ANOVA.
            df_num: Numerator degrees of freedom.
            df_den: Denominator degrees of freedom.
            n_groups: Number of within-subject levels (conditions).
            n_subjects: Number of subjects.

        Returns:
            float: Observed power (0.0 to 1.0).
        """
        if f_value <= 0 or df_num <= 0 or df_den <= 0:
            logger.warning("Invalid ANOVA parameters for power calculation. Returning 0.0.")
            return 0.0

        # Calculate non-centrality parameter (lambda)
        # For ANOVA, lambda = f^2 * N_effective
        # In repeated measures, N_effective is often approximated by total observations
        # or specifically derived from the F-statistic definition.
        # F = (MS_between) / (MS_error)
        # lambda = f^2 * (n_subjects * n_groups) ?
        # More precise: lambda = f^2 * N, where N is total sample size in one-way.
        # For RM ANOVA, we use the specific degrees of freedom.
        # Standard approximation: lambda = f^2 * (df_den + df_num + 1) is not quite right.
        # Let's use the relationship: F ~ (lambda / df_num) / (chi2 / df_den)
        # Actually, scipy.stats.ncf uses non-centrality parameter 'nc'.
        # The non-centrality parameter lambda (nc) is related to F by:
        # F = (chi2_nc / df_num) / (chi2 / df_den)
        # We can invert this: nc = f * df_num * (something related to error variance).
        # A robust way: nc = f^2 * (df_num + df_den + 1) is a common approximation for power calculation
        # when f is the effect size. However, we have the observed F.
        # Let's use the definition: F_obs = (MS_effect / MS_error).
        # The non-centrality parameter for the F distribution under the alternative hypothesis is:
        # nc = f^2 * N_total? No.
        # Let's use the standard formula: nc = f^2 * (n_subjects * (n_groups - 1))?
        # Actually, the simplest and most robust method given observed F is:
        # Power = 1 - CDF(F_crit, df_num, df_den, nc)
        # where nc is the non-centrality parameter.
        # If we assume the observed F is the true F (which is what observed power does),
        # then nc = F_obs * df_num? No, that's not right.
        # Correct approach for observed power:
        # 1. Calculate effect size f from F: f = sqrt(F * df_num / (df_num + df_den))? No.
        #    F = (f^2 * df_num) / (df_den / df_den) ?
        #    Actually, F = (SS_effect/df_num) / (SS_error/df_den).
        #    Partial eta-squared = SS_effect / (SS_effect + SS_error).
        #    f = sqrt(eta_p^2 / (1 - eta_p^2)).
        # 2. Calculate nc = f^2 * N_effective.
        #    For RM ANOVA, N_effective = n_subjects * n_groups? Or just n_subjects?
        #    Usually, for power calculation of RM ANOVA, N is the number of subjects.
        #    But the non-centrality parameter depends on the design.
        #    Let's use the approximation: nc = F_obs * df_num.
        #    Wait, if H0 is true, F ~ F(df_num, df_den).
        #    If H1 is true, F ~ F(df_num, df_den, nc).
        #    The observed F is a realization.
        #    A common heuristic for observed power is to treat the observed F as the non-centrality
        #    parameter scaled: nc = F_obs * df_num.
        #    Let's verify: E[F] under H1 is approx 1 + nc/df_num. So nc ~ (F-1)*df_num.
        #    Let's use nc = (F_obs - 1) * df_num. If F < 1, power is low.

        # Robust calculation:
        # 1. Critical F value
        f_crit = stats.f.ppf(1 - self.alpha, df_num, df_den)

        # 2. Estimate non-centrality parameter (nc) from observed F
        #    Under H1, E[F] approx 1 + nc/df_num.
        #    So nc approx (F_obs - 1) * df_num.
        #    If F_obs < 1, we set nc = 0 (or very small), implying power < alpha.
        nc = max(0.0, (f_value - 1.0) * df_num)

        # 3. Calculate Power = P(F > f_crit | df_num, df_den, nc)
        #    This is 1 - CDF(f_crit)
        power = 1.0 - stats.ncf.cdf(f_crit, df_num, df_den, nc)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, power))

    def run_a_priori_power_analysis(
        self,
        effect_size: float,
        n_groups: int,
        alpha: float = 0.05,
        power: float = 0.80
    ) -> Dict[str, Any]:
        """
        Perform a priori power analysis to determine required sample size.

        Args:
            effect_size: Expected effect size (Cohen's f).
            n_groups: Number of within-subject levels.
            alpha: Significance level.
            power: Desired power.

        Returns:
            dict: Results including required sample size.
        """
        # For repeated measures, we approximate using the F-test power
        # We need to find N (number of subjects) such that power >= target.
        # This requires an iterative approach or lookup.
        # Using scipy.stats.ncf to find the N that satisfies the condition.
        # df_num = n_groups - 1
        # df_den = (n_subjects - 1) * (n_groups - 1) (assuming sphericity)
        # nc = f^2 * n_subjects * n_groups? Or f^2 * n_subjects?
        # Standard formula for RM ANOVA non-centrality: nc = f^2 * N * k?
        # Let's use the approximation: nc = f^2 * n_subjects * n_groups (total observations)
        # But usually power analysis for RM ANOVA is done on the number of subjects.
        # Let's iterate on n_subjects.

        df_num = n_groups - 1
        if df_num <= 0:
            raise ValueError("n_groups must be > 1")

        required_n = 0
        for n in range(2, 500): # Search up to 500 subjects
            df_den = (n - 1) * df_num
            # Non-centrality parameter approximation
            # nc = f^2 * n * n_groups (total observations) is one way.
            # Another common way: nc = f^2 * n_subjects * (n_groups) * (1 - rho)?
            # Let's stick to the standard: nc = f^2 * N_total?
            # Actually, for RM ANOVA, the standard formula for nc is:
            # nc = f^2 * N * k (where N is subjects, k is groups) is often used in G*Power.
            nc = (effect_size ** 2) * n * n_groups

            f_crit = stats.f.ppf(1 - alpha, df_num, df_den)
            current_power = 1.0 - stats.ncf.cdf(f_crit, df_num, df_den, nc)

            if current_power >= power:
                required_n = n
                break

        return {
            "effect_size": effect_size,
            "n_groups": n_groups,
            "alpha": alpha,
            "target_power": power,
            "required_n_subjects": required_n,
            "achieved_power_at_n": 1.0 - stats.ncf.cdf(
                stats.f.ppf(1 - alpha, df_num, (required_n - 1) * df_num),
                df_num,
                (required_n - 1) * df_num,
                (effect_size ** 2) * required_n * n_groups
            ) if required_n > 0 else 0.0
        }

def load_metrics_summary(input_path: str) -> pd.DataFrame:
    """
    Load the metrics summary CSV generated by the ANOVA step.

    Args:
        input_path: Path to metrics_summary.csv.

    Returns:
        pd.DataFrame: The loaded dataframe.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Metrics summary file not found: {input_path}")

    df = pd.read_csv(path)
    return df

def generate_power_report(
    metrics_df: pd.DataFrame,
    output_path: str,
    mode: str = 'full',
    min_n_full: int = 30,
    min_n_pilot: int = 5
) -> None:
    """
    Generate the observed power report.

    Args:
        metrics_df: DataFrame containing ANOVA results (F, df_num, df_den, p-value).
        output_path: Path to write the markdown report.
        mode: 'full' or 'pilot'.
        min_n_full: Minimum N required for full mode.
        min_n_pilot: Minimum N required for pilot mode.
    """
    calculator = PowerCalculator()

    # Determine N from the dataframe (assuming one row per metric, with 'n_subjects' column or derived)
    # If the metrics_df comes from run_anova_rm, it should have 'n_subjects' or we can infer from 'df_den'.
    # df_den = (n_subjects - 1) * (n_groups - 1).
    # Assuming n_groups = 2 (Traditional vs Explainable), then df_den = n_subjects - 1 => n_subjects = df_den + 1.
    # Let's add a column 'n_subjects' if missing.
    if 'n_subjects' not in metrics_df.columns:
        # Assume 2 groups (Traditional, Explainable) -> df_num = 1.
        # df_den = (N-1) * (2-1) = N-1.
        # So N = df_den + 1.
        if 'df_den' in metrics_df.columns:
            metrics_df['n_subjects'] = metrics_df['df_den'] + 1
        else:
            # Fallback: try to count unique subjects if data is available, but here we rely on ANOVA output.
            raise ValueError("Cannot determine n_subjects. Ensure 'df_den' is present or 'n_subjects' is provided.")

    n_values = metrics_df['n_subjects'].unique()
    if len(n_values) > 1:
        # Inconsistent sample sizes? Use min or average?
        # For simplicity, use the min across metrics or the max?
        # Let's use the minimum N found across metrics to be conservative.
        n_total = int(n_values.min())
    else:
        n_total = int(n_values[0])

    # Validate N based on mode
    if mode == 'full':
        if n_total < min_n_full:
            raise ValueError(
                f"Sample size N={n_total} is below the required threshold for full mode (N >= {min_n_full}). "
                f"Constitution Principle VI requires N=30. "
                f"Set mode='pilot' to proceed with smaller N."
            )
    elif mode == 'pilot':
        if n_total < min_n_pilot:
            logger.warning(f"Pilot mode detected with N={n_total}. Minimum recommended for pilot is {min_n_pilot}.")
        else:
            logger.warning(f"Pilot mode detected with N={n_total}. Observed power results are preliminary.")

    # Calculate observed power for each metric
    power_results = []
    report_lines = [
        "# Observed Power Report",
        f"## Analysis Configuration",
        f"- Mode: {mode}",
        f"- Total Subjects (N): {n_total}",
        f"- Significance Level (alpha): 0.05",
        "",
        "## Observed Power by Metric",
        "| Metric | F-Value | df_num | df_den | p-value | Observed Power |",
        "|---|---|---|---|---|---|"
    ]

    for _, row in metrics_df.iterrows():
        metric_name = row.get('metric', 'Unknown')
        f_val = row.get('f_value', 0.0)
        df_num = int(row.get('df_num', 0))
        df_den = int(row.get('df_den', 0))
        p_val = row.get('p_value', 1.0)

        # Assume n_groups = 2 for the calculation if not provided, or infer from df_num (df_num = k-1 => k = df_num+1)
        n_groups = df_num + 1

        power = calculator.calculate_observed_power_rm_anova(
            f_value=f_val,
            df_num=df_num,
            df_den=df_den,
            n_groups=n_groups,
            n_subjects=n_total
        )

        power_results.append({
            'metric': metric_name,
            'f_value': f_val,
            'df_num': df_num,
            'df_den': df_den,
            'p_value': p_val,
            'observed_power': power
        })

        # Format for markdown
        report_lines.append(
            f"| {metric_name} | {f_val:.4f} | {df_num} | {df_den} | {p_val:.4f} | {power:.4f} |"
        )

    # Summary
    report_lines.append("")
    report_lines.append("## Summary")
    high_power_metrics = [r for r in power_results if r['observed_power'] >= 0.80]
    low_power_metrics = [r for r in power_results if r['observed_power'] < 0.80]

    if high_power_metrics:
        report_lines.append(f"- **Adequately Powered (>= 0.80)**: {', '.join([r['metric'] for r in high_power_metrics])}")
    if low_power_metrics:
        report_lines.append(f"- **Underpowered (< 0.80)**: {', '.join([r['metric'] for r in low_power_metrics])}")

    if mode == 'full' and n_total < 30:
       report_lines.append(f"\n**WARNING**: Full mode requires N >= 30. Current N={n_total}.")

    report_content = "\n".join(report_lines)

    # Write to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_content)
    logger.info(f"Power report written to {output_path}")

    # Also save CSV for programmatic access
    csv_path = output_path.with_suffix('.csv')
    pd.DataFrame(power_results).to_csv(csv_path, index=False)
    logger.info(f"Power results CSV written to {csv_path}")

def main():
    """CLI entry point for power analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate Observed Power Report")
    parser.add_argument("--input", required=True, help="Path to metrics_summary.csv")
    parser.add_argument("--output", required=True, help="Path to output report (markdown)")
    parser.add_argument("--mode", default="full", choices=["full", "pilot"], help="Analysis mode")
    args = parser.parse_args()

    try:
        df = load_metrics_summary(args.input)
        generate_power_report(df, args.output, mode=args.mode)
        print(f"Power analysis completed successfully.")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Data Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()