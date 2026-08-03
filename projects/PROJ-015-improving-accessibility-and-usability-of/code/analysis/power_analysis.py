"""
Power analysis module for computing observed effect size, statistical power, and required sample size.

This module implements the PowerCalculator class to perform power analysis based on
Repeated Measures ANOVA results. It computes eta-squared as the effect size,
statistical power at alpha=0.05, and the required sample size to achieve 80% power.

Output: data/processed/power_flags.json containing power, required_N, effect_size, and flag.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import json
from utils.logger import get_logger

logger = get_logger(__name__)

class PowerCalculator:
    """
    Calculator for statistical power analysis based on ANOVA results.
    
    Computes:
    - Observed effect size (eta-squared, η²)
    - Statistical power (at α=0.05)
    - Required sample size (to achieve 80% power)
    """
    
    def __init__(self, alpha: float = 0.05, target_power: float = 0.80):
        """
        Initialize the PowerCalculator.
        
        Args:
            alpha: Significance level (default: 0.05)
            target_power: Target statistical power (default: 0.80)
        """
        self.alpha = alpha
        self.target_power = target_power
        
    def compute_effect_size_eta_squared(
        self, 
        ss_between: float, 
        ss_within: float, 
        ss_error: float = None
    ) -> float:
        """
        Compute eta-squared (η²) effect size.
        
        For repeated measures ANOVA: η² = SS_between / (SS_between + SS_error)
        
        Args:
            ss_between: Sum of squares between conditions
            ss_within: Sum of squares within conditions (total - between)
            ss_error: Sum of squares error (if None, uses ss_within)
        
        Returns:
            Eta-squared effect size value
        """
        if ss_error is None:
            ss_error = ss_within
        
        total_ss = ss_between + ss_error
        if total_ss == 0:
            logger.warning("Total sum of squares is zero, returning 0 for effect size")
            return 0.0
        
        eta_squared = ss_between / total_ss
        return eta_squared
    
    def compute_power_from_effect_size(
        self, 
        effect_size: float, 
        n_obs: int, 
        n_groups: int, 
        n_subjects: int, 
        alpha: float = None
    ) -> float:
        """
        Compute statistical power using the non-central F-distribution.
        
        Args:
            effect_size: Eta-squared effect size
            n_obs: Total number of observations
            n_groups: Number of groups/conditions
            n_subjects: Number of subjects
            alpha: Significance level (uses self.alpha if None)
        
        Returns:
            Statistical power value (0-1)
        """
        if alpha is None:
            alpha = self.alpha
        
        # Degrees of freedom
        df1 = n_groups - 1  # numerator df
        df2 = (n_subjects - 1) * (n_groups - 1)  # denominator df for repeated measures
        
        # Non-centrality parameter (lambda)
        # For eta-squared: λ = f² * (df1 + df2 + 1) where f² = η² / (1 - η²)
        if effect_size >= 1.0:
            effect_size = 0.999  # Cap to avoid division by zero
        if effect_size <= 0:
            return 0.0
        
        f_squared = effect_size / (1 - effect_size)
        ncp = f_squared * (df1 + df2 + 1)
        
        # Critical F value
        f_crit = stats.f.ppf(1 - alpha, df1, df2)
        
        # Power = P(F > f_crit | H1) = 1 - CDF(f_crit)
        power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
        
        return max(0.0, min(1.0, power))
    
    def compute_required_n(
        self, 
        effect_size: float, 
        n_groups: int, 
        alpha: float = None, 
        target_power: float = None
    ) -> int:
        """
        Compute required sample size (number of subjects) to achieve target power.
        
        Uses iterative search to find minimum N.
        
        Args:
            effect_size: Eta-squared effect size
            n_groups: Number of groups/conditions
            alpha: Significance level (uses self.alpha if None)
            target_power: Target power (uses self.target_power if None)
        
        Returns:
            Required number of subjects
        """
        if alpha is None:
            alpha = self.alpha
        if target_power is None:
            target_power = self.target_power
        
        if effect_size <= 0:
            logger.warning("Effect size is zero or negative, returning max N")
            return 1000  # Return a large number
        
        df1 = n_groups - 1
        
        # Iterative search for required N
        n_subjects = 2  # Start with minimum possible
        max_n = 1000  # Upper bound
        
        while n_subjects <= max_n:
            df2 = (n_subjects - 1) * df1
            
            # Non-centrality parameter
            if effect_size >= 1.0:
                effect_size = 0.999
            f_squared = effect_size / (1 - effect_size)
            ncp = f_squared * (df1 + df2 + 1)
            
            # Critical F value
            f_crit = stats.f.ppf(1 - alpha, df1, df2)
            
            # Current power
            current_power = 1 - stats.ncf.cdf(f_crit, df1, df2, ncp)
            
            if current_power >= target_power:
                return n_subjects
            
            n_subjects += 1
        
        logger.warning(f"Could not achieve target power {target_power} with effect size {effect_size}")
        return max_n
    
    def analyze_from_anova_results(
        self, 
        ss_between: float, 
        ss_error: float, 
        n_subjects: int, 
        n_groups: int, 
        f_stat: float, 
        p_value: float
    ) -> Dict[str, Any]:
        """
        Perform complete power analysis from ANOVA results.
        
        Args:
            ss_between: Sum of squares between conditions
            ss_error: Sum of squares error
            n_subjects: Number of subjects
            n_groups: Number of groups/conditions
            f_stat: F-statistic from ANOVA
            p_value: P-value from ANOVA
        
        Returns:
            Dictionary with power analysis results
        """
        # Compute effect size
        effect_size = self.compute_effect_size_eta_squared(ss_between, ss_error)
        
        # Compute observed power
        observed_power = self.compute_power_from_effect_size(
            effect_size, 
            n_subjects * n_groups, 
            n_groups, 
            n_subjects, 
            self.alpha
        )
        
        # Compute required N
        required_n = self.compute_required_n(effect_size, n_groups, self.alpha, self.target_power)
        
        # Determine flag based on constitutional threshold (N >= 30)
        constitutional_threshold = 30
        flag = "sufficient" if n_subjects >= constitutional_threshold else "insufficient"
        
        # Also flag if power is below target
        if observed_power < self.target_power:
            flag = "underpowered"
        
        return {
            "power": round(observed_power, 4),
            "required_N": required_n,
            "effect_size": round(effect_size, 6),
            "flag": flag,
            "n_subjects": n_subjects,
            "n_groups": n_groups,
            "alpha": self.alpha,
            "target_power": self.target_power,
            "constitutional_threshold": constitutional_threshold,
            "f_statistic": round(f_stat, 4),
            "p_value": round(p_value, 6)
        }
    
    def analyze_from_dataframe(
        self, 
        df: pd.DataFrame, 
        subject_col: str, 
        group_col: str, 
        value_col: str
    ) -> Dict[str, Any]:
        """
        Perform power analysis directly from a DataFrame.
        
        Args:
            df: DataFrame with session data
            subject_col: Column name for subject/participant ID
            group_col: Column name for condition/group
            value_col: Column name for the metric value
        
        Returns:
            Dictionary with power analysis results
        """
        # Get unique counts
        n_subjects = df[subject_col].nunique()
        n_groups = df[group_col].nunique()
        
        if n_subjects < 2 or n_groups < 2:
            logger.error("Need at least 2 subjects and 2 groups for power analysis")
            return {
                "power": 0.0,
                "required_N": 1000,
                "effect_size": 0.0,
                "flag": "insufficient_data",
                "error": "Need at least 2 subjects and 2 groups"
            }
        
        # Compute ANOVA manually to get SS values
        # Group by conditions and compute sums of squares
        grand_mean = df[value_col].mean()
        n_obs = len(df)
        
        # SS_total
        ss_total = ((df[value_col] - grand_mean) ** 2).sum()
        
        # SS_between (groups)
        group_means = df.groupby(group_col)[value_col].mean()
        ss_between = sum(
            len(df[df[group_col] == g]) * (m - grand_mean) ** 2 
            for g, m in group_means.items()
        )
        
        # SS_subjects (for repeated measures)
        subject_means = df.groupby(subject_col)[value_col].mean()
        ss_subjects = sum(
            len(df[df[subject_col] == s]) * (m - grand_mean) ** 2 
            for s, m in subject_means.items()
        )
        
        # SS_error = SS_total - SS_between - SS_subjects
        ss_error = ss_total - ss_between - ss_subjects
        
        # Degrees of freedom
        df_between = n_groups - 1
        df_error = (n_subjects - 1) * (n_groups - 1)
        
        # Mean squares
        ms_between = ss_between / df_between if df_between > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0
        
        # F-statistic
        f_stat = ms_between / ms_error if ms_error > 0 else 0
        
        # P-value
        p_value = 1 - stats.f.cdf(f_stat, df_between, df_error) if df_error > 0 else 1.0
        
        # Perform power analysis
        return self.analyze_from_anova_results(
            ss_between=ss_between,
            ss_error=ss_error,
            n_subjects=n_subjects,
            n_groups=n_groups,
            f_stat=f_stat,
            p_value=p_value
        )

def main():
    """
    Main function to run power analysis on cleaned data.
    
    Reads cleaned_sessions.csv, performs power analysis for each metric,
    and writes results to data/processed/power_flags.json.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run power analysis on cleaned data")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/cleaned_sessions.csv",
        help="Path to cleaned sessions CSV"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/power_flags.json",
        help="Path to output JSON file"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level"
    )
    parser.add_argument(
        "--target-power",
        type=float,
        default=0.80,
        help="Target statistical power"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting power analysis")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    
    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        logger.error("Cannot run power analysis without cleaned data. Run clean_data.py first.")
        sys.exit(1)
    
    # Load cleaned data
    try:
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} sessions from {args.input}")
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    # Check for required columns
    required_cols = ['participant_id', 'interface_type', 'completion_time', 'error_count', 'sus_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
    
    # Initialize calculator
    calculator = PowerCalculator(alpha=args.alpha, target_power=args.target_power)
    
    # Perform power analysis for each metric
    metrics = ['completion_time', 'error_count', 'sus_score']
    results = {}
    
    for metric in metrics:
        logger.info(f"Analyzing power for {metric}")
        
        # Filter out missing values
        metric_df = df.dropna(subset=[metric])
        
        if len(metric_df) < 10:
            logger.warning(f"Insufficient data for {metric}: {len(metric_df)} rows")
            results[metric] = {
                "power": 0.0,
                "required_N": 1000,
                "effect_size": 0.0,
                "flag": "insufficient_data",
                "n_subjects": len(metric_df['participant_id'].nunique()) if len(metric_df) > 0 else 0
            }
            continue
        
        try:
            analysis = calculator.analyze_from_dataframe(
                df=metric_df,
                subject_col='participant_id',
                group_col='interface_type',
                value_col=metric
            )
            results[metric] = analysis
            logger.info(f"  Effect size (η²): {analysis['effect_size']:.4f}")
            logger.info(f"  Observed power: {analysis['power']:.4f}")
            logger.info(f"  Required N: {analysis['required_N']}")
            logger.info(f"  Flag: {analysis['flag']}")
        except Exception as e:
            logger.error(f"Error analyzing {metric}: {e}")
            results[metric] = {
                "power": 0.0,
                "required_N": 1000,
                "effect_size": 0.0,
                "flag": "error",
                "error": str(e)
            }
    
    # Write results to JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis results written to {args.output}")
    
    # Summary
    logger.info("=" * 50)
    logger.info("POWER ANALYSIS SUMMARY")
    logger.info("=" * 50)
    for metric, result in results.items():
        logger.info(f"{metric}:")
        logger.info(f"  η² = {result['effect_size']:.4f}")
        logger.info(f"  Power = {result['power']:.4f}")
        logger.info(f"  Required N = {result['required_N']}")
        logger.info(f"  Status = {result['flag']}")
    
    return results

if __name__ == "__main__":
    main()