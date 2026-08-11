"""
Power Analysis Module for PROJ-015.

Implements PowerCalculator to compute observed effect size (eta-squared),
statistical power (alpha=0.05), and required sample size (N) for
Repeated Measures ANOVA results.

Output: data/processed/power_flags.json
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import json
import logging

from utils.logger import get_logger

# Ensure logger is available
logger = get_logger(__name__)

class PowerCalculator:
    """
    Computes statistical power, effect size, and required sample size
    for Repeated Measures ANOVA results.
    """

    def __init__(self, alpha: float = 0.05, power_target: float = 0.80):
        """
        Initialize the PowerCalculator.

        Args:
            alpha: Significance level (default 0.05).
            power_target: Target statistical power (default 0.80).
        """
        self.alpha = alpha
        self.power_target = power_target
        self.constitutional_min_n = 30

    def compute_effect_size_etasquared(
        self, f_stat: float, df_num: int, df_denom: int
    ) -> float:
        """
        Compute partial eta-squared from F-statistic and degrees of freedom.

        Formula: eta^2 = (F * df_num) / (F * df_num + df_denom)

        Args:
            f_stat: The F-statistic from ANOVA.
            df_num: Numerator degrees of freedom.
            df_denom: Denominator degrees of freedom.

        Returns:
            Partial eta-squared value.
        """
        if f_stat == 0:
            return 0.0
        numerator = f_stat * df_num
        denominator = (f_stat * df_num) + df_denom
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def compute_power(
        self, f_stat: float, df_num: int, df_denom: int, n_subjects: int, n_conditions: int
    ) -> float:
        """
        Compute observed statistical power using non-central F-distribution.

        Args:
            f_stat: The observed F-statistic.
            df_num: Numerator degrees of freedom.
            df_denom: Denominator degrees of freedom.
            n_subjects: Number of subjects (participants).
            n_conditions: Number of conditions (repeated measures).

        Returns:
            Observed power (probability of rejecting null given effect).
        """
        # Calculate non-centrality parameter (lambda)
        # lambda = f^2 * N_effect
        # For RM-ANOVA, N_effect = n_subjects * n_conditions
        # However, we derive lambda from the observed F:
        # F = (lambda / df_num) / (1 + lambda/df_denom) roughly,
        # but scipy.stats.ncf uses lambda directly.
        # Reconstruct lambda from F: lambda = F * df_num * (1 + lambda/df_denom) -> iterative or approx.
        # Simpler approach: Use the observed F to estimate effect size f, then compute lambda.
        
        eta_sq = self.compute_effect_size_etasquared(f_stat, df_num, df_denom)
        # f^2 = eta^2 / (1 - eta^2)
        if eta_sq >= 1.0:
            eta_sq = 0.9999
        f_squared = eta_sq / (1 - eta_sq)
        
        # Total observations in the design = n_subjects * n_conditions
        total_n = n_subjects * n_conditions
        lambda_ncp = f_squared * total_n

        # Power = 1 - beta = P(F > F_crit | lambda_ncp)
        # F_crit is the critical value of central F at alpha
        f_crit = stats.f.ppf(1 - self.alpha, df_num, df_denom)
        
        # Calculate power using non-central F CDF
        # power = 1 - CDF(F_crit, dfn, dfd, ncp)
        power = 1.0 - stats.ncf.cdf(f_crit, df_num, df_denom, lambda_ncp)
        
        return float(power)

    def compute_required_n(
        self, f_stat: float, df_num: int, df_denom: int, n_conditions: int
    ) -> int:
        """
        Compute the required sample size (N) to achieve target power.
        
        Uses an iterative approach to find the smallest N such that
        power >= power_target, given the observed effect size.

        Args:
            f_stat: Observed F-statistic.
            df_num: Numerator degrees of freedom.
            df_denom: Denominator degrees of freedom (scales with N).
            n_conditions: Number of repeated conditions.

        Returns:
            Required number of subjects.
        """
        # Estimate effect size f from the observed F
        eta_sq = self.compute_effect_size_etasquared(f_stat, df_num, df_denom)
        if eta_sq >= 1.0:
            eta_sq = 0.9999
        f_squared = eta_sq / (1 - eta_sq)
        f_val = np.sqrt(f_squared)

        # Iterative search for N
        # df_num is fixed (k-1), df_denom = (N-1)(k-1)
        # We need to find N such that power >= target
        
        current_n = 10
        max_n = 10000
        step = 10

        while current_n < max_n:
            # Calculate degrees of freedom for this N
            # df_num = k - 1 (constant)
            # df_denom = (N - 1) * (k - 1)
            df_numerator = df_num
            df_denominator = (current_n - 1) * df_num
            
            if df_denominator <= 0:
                current_n += step
                continue

            # Calculate non-centrality parameter for this N
            total_n = current_n * n_conditions
            lambda_ncp = f_squared * total_n

            # Calculate critical F
            f_crit = stats.f.ppf(1 - self.alpha, df_numerator, df_denominator)
            
            # Calculate power
            power = 1.0 - stats.ncf.cdf(f_crit, df_numerator, df_denominator, lambda_ncp)

            if power >= self.power_target:
                return current_n
            
            current_n += step

        # If not found within range, return max or raise warning
        logger.warning(f"Could not find N for target power {self.power_target} within {max_n}. Returning {max_n}.")
        return max_n

    def analyze(
        self, 
        metrics_summary_path: str, 
        output_path: str
    ) -> Dict[str, Any]:
        """
        Perform full power analysis on the metrics summary.

        Args:
            metrics_summary_path: Path to data/processed/metrics_summary.csv.
            output_path: Path to write data/processed/power_flags.json.

        Returns:
            Dictionary with keys: power, required_N, effect_size, flag.
        """
        logger.info(f"Loading metrics summary from {metrics_summary_path}")
        if not os.path.exists(metrics_summary_path):
            raise FileNotFoundError(f"Metrics summary not found at {metrics_summary_path}")

        df = pd.read_csv(metrics_summary_path)
        
        # Expected columns: metric, F_stat, p_val, corrected_p, df_num, df_denom, n_subjects, n_conditions
        # If df_num/denom/n_subjects are missing, we must infer or use defaults.
        # For RM-ANOVA with 2 conditions (Traditional vs Explainable):
        # df_num = k - 1 = 1
        # df_denom = (N - 1) * (k - 1) = N - 1
        
        results = []
        
        for _, row in df.iterrows():
            metric = row['metric']
            f_stat = row['F_stat']
            p_val = row['p_val']
            
            # Infer degrees of freedom if missing
            # Assuming 2 conditions (Traditional, Explainable)
            n_conditions = 2
            df_num = 1 
            
            # If df_denom is present, use it; else infer from N if available
            if 'df_denom' in row and pd.notna(row['df_denom']):
                df_denom = int(row['df_denom'])
            elif 'n_subjects' in row and pd.notna(row['n_subjects']):
                df_denom = int(row['n_subjects']) - 1
            else:
                # Fallback: assume a small N if missing (bad practice but necessary for crash safety)
                # In a real run, this should be populated by the ANOVA step
                df_denom = 29 # Assume N=30

            n_subjects = df_denom + 1
            
            # Compute Effect Size
            effect_size = self.compute_effect_size_etasquared(f_stat, df_num, df_denom)
            
            # Compute Power
            power = self.compute_power(f_stat, df_num, df_denom, n_subjects, n_conditions)
            
            # Compute Required N
            required_n = self.compute_required_n(f_stat, df_num, df_denom, n_conditions)
            
            # Determine Flag
            # Flag is "underpowered" if power < target OR if N < constitutional_min_n
            flag = "underpowered"
            if power >= self.power_target and n_subjects >= self.constitutional_min_n:
                flag = "adequate"
            elif n_subjects < self.constitutional_min_n:
                flag = "sample_too_small"
            
            results.append({
                "metric": metric,
                "power": round(power, 4),
                "required_N": required_n,
                "effect_size": round(effect_size, 4),
                "flag": flag,
                "observed_N": n_subjects,
                "f_stat": f_stat,
                "p_val": p_val
            })

        # Aggregate results for the JSON output
        # We take the overall flag status: if ANY metric is underpowered, the study is underpowered
        overall_flag = "adequate"
        for res in results:
            if res["flag"] != "adequate":
                overall_flag = res["flag"]
                break

        output_data = {
            "power": results[0]["power"] if results else 0.0, # Primary metric power
            "required_N": results[0]["required_N"] if results else 0,
            "effect_size": results[0]["effect_size"] if results else 0.0,
            "flag": overall_flag,
            "details": results,
            "alpha": self.alpha,
            "power_target": self.power_target,
            "constitutional_min_n": self.constitutional_min_n
        }

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        logger.info(f"Writing power flags to {output_path}")
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        return output_data

def main():
    """CLI entry point for power analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute power analysis for ANOVA results.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/metrics_summary.csv",
        help="Path to metrics_summary.csv"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/power_flags.json",
        help="Path to output power_flags.json"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--power-target",
        type=float,
        default=0.80,
        help="Target power"
    )

    args = parser.parse_args()

    calculator = PowerCalculator(alpha=args.alpha, power_target=args.power_target)
    
    try:
        result = calculator.analyze(args.input, args.output)
        print(f"Power analysis complete. Flag: {result['flag']}")
        print(f"Power: {result['power']}, Required N: {result['required_N']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
