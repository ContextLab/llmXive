"""
Power analysis for the AdaPlanBench extension study.

This module calculates the achieved power for the GLMM given the sample size
from the execution traces.
"""
import os
import sys
import json
import argparse
import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import statsmodels.stats.power as smp

# Import project configuration
from config import get_paths, get_analysis_config

# Constants
DEFAULT_ALPHA = 0.05
DEFAULT_EFFECT_SIZE = 0.15  # Cohen's f² target
DEFAULT_GROUPS = 2  # Monolithic vs Dual-track

def load_execution_traces(input_path: str) -> pd.DataFrame:
    """Load the execution traces CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Execution traces file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['task_id', 'architecture', 'constraint_count', 'violation_boolean', 'final_score']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in execution traces: {missing_cols}")
    
    return df

def calculate_effect_size_for_logistic(df: pd.DataFrame) -> float:
    """
    Calculate effect size for logistic regression (violation_boolean as outcome).
    
    Uses the proportion of violations in each group to estimate effect size.
    This is a simplified approach; for GLMM, we'd typically use simulation-based power.
    Here we use a proxy based on group proportions.
    """
    # Group by architecture and calculate violation rate
    violation_rates = df.groupby('architecture')['violation_boolean'].mean()
    
    if len(violation_rates) < 2:
        # If only one group, we can't calculate effect size
        return DEFAULT_EFFECT_SIZE
    
    # Calculate Cohen's h for proportions
    p1 = violation_rates.iloc[0]
    p2 = violation_rates.iloc[1]
    
    # Avoid division by zero or log of zero
    p1 = max(0.001, min(0.999, p1))
    p2 = max(0.001, min(0.999, p2))
    
    # Cohen's h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
    h = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
    
    # Convert to a rough f² equivalent (approximate)
    # This is a heuristic; exact conversion depends on model specifics
    f_squared = (h ** 2) / 4
    
    return f_squared if f_squared > 0 else DEFAULT_EFFECT_SIZE

def estimate_required_sample_size(effect_size: float, alpha: float = DEFAULT_ALPHA, 
                                 power: float = 0.80, groups: int = DEFAULT_GROUPS) -> int:
    """
    Estimate the required sample size for detecting the given effect size.
    
    Uses statsmodels' FTestAnovaPower for a rough approximation.
    For GLMM with binary outcomes, this is an approximation.
    """
    # Use F-test power analysis as an approximation
    # For logistic regression with binary outcome, we can use G*Power-like approximations
    # Here we use a simplified approach based on the number of groups and effect size
    
    # Approximate formula for two-group comparison with binary outcome
    # n per group = 2 * (Z_alpha/2 + Z_beta)^2 * p * (1-p) / (p1 - p2)^2
    # We'll use statsmodels for a more robust calculation
    
    try:
        # Use FTestPower for a rough approximation
        from statsmodels.stats.power import FTestAnovaPower
        analysis = FTestAnovaPower()
        
        # Effect size f for ANOVA (approximate conversion from f²)
        f = math.sqrt(effect_size)
        
        # Calculate required sample size
        n_per_group = analysis.solve_power(effect_size=f, alpha=alpha, power=power, 
                                         k_groups=groups, axis=0)
        
        if n_per_group is None or n_per_group < 0:
            return int(100 / groups)  # Default fallback
        
        return int(n_per_group * groups)  # Total sample size
    except Exception:
        # Fallback to a simple rule of thumb
        # For binary outcomes, typically need ~10-20 observations per predictor
        # With 2 groups and interaction, we need at least 40-60 observations
        return 60

def perform_power_analysis(df: pd.DataFrame, effect_size: float = DEFAULT_EFFECT_SIZE,
                          alpha: float = DEFAULT_ALPHA, 
                          groups: int = DEFAULT_GROUPS) -> Dict[str, Any]:
    """
    Perform power analysis on the execution traces.
    
    Calculates the achieved power given the sample size and effect size.
    """
    n_observations = len(df)
    
    if n_observations == 0:
        raise ValueError("No observations found in execution traces")
    
    # If effect_size is not provided, estimate it from the data
    if effect_size == DEFAULT_EFFECT_SIZE:
        effect_size = calculate_effect_size_for_logistic(df)
    
    # Estimate required sample size for 80% power
    required_n = estimate_required_sample_size(effect_size, alpha, power=0.80, groups=groups)
    
    # Calculate achieved power
    # Using F-test power analysis as an approximation
    try:
        from statsmodels.stats.power import FTestAnovaPower
        analysis = FTestAnovaPower()
        
        f = math.sqrt(effect_size)
        
        # Calculate power for the actual sample size
        achieved_power = analysis.power(effect_size=f, nobs1=n_observations/groups, 
                                      alpha=alpha, k_groups=groups)
        
        if achieved_power is None or math.isnan(achieved_power):
            achieved_power = 0.0
    except Exception:
        # Fallback: if we can't calculate, estimate based on sample size
        # Rough rule: power increases with sqrt(n)
        if required_n > 0:
            achieved_power = min(0.99, 0.80 * math.sqrt(n_observations / required_n))
        else:
            achieved_power = 0.5  # Default guess
    
    return {
        'calculated_power': float(achieved_power),
        'effect_size': float(effect_size),
        'sample_size': int(n_observations),
        'groups': int(groups),
        'required_sample_size_for_80_power': int(required_n),
        'alpha': float(alpha)
    }

def run_power_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main function to run power analysis and save results.
    
    Args:
        input_path: Path to execution_traces.csv
        output_path: Path to save power_report.json
    
    Returns:
        Dictionary with power analysis results
    """
    # Load execution traces
    df = load_execution_traces(input_path)
    
    # Perform power analysis
    results = perform_power_analysis(df)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """Command-line interface for power analysis."""
    parser = argparse.ArgumentParser(description='Perform power analysis on execution traces')
    parser.add_argument('--input', type=str, 
                      default='data/processed/execution_traces.csv',
                      help='Path to execution_traces.csv')
    parser.add_argument('--output', type=str,
                      default='data/processed/power_report.json',
                      help='Path to save power_report.json')
    parser.add_argument('--effect-size', type=float, default=DEFAULT_EFFECT_SIZE,
                      help='Effect size (Cohen\'s f²)')
    parser.add_argument('--alpha', type=float, default=DEFAULT_ALPHA,
                      help='Significance level')
    parser.add_argument('--groups', type=int, default=DEFAULT_GROUPS,
                      help='Number of groups')
    
    args = parser.parse_args()
    
    try:
        results = run_power_analysis(args.input, args.output)
        
        # Log results
        print(f"Power analysis completed:")
        print(f"  Sample size: {results['sample_size']}")
        print(f"  Effect size: {results['effect_size']:.4f}")
        print(f"  Calculated power: {results['calculated_power']:.4f}")
        print(f"  Required sample size for 80% power: {results['required_sample_size_for_80_power']}")
        print(f"  Results saved to: {args.output}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during power analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()