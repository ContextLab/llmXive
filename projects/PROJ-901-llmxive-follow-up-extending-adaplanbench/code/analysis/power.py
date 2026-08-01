"""
Power analysis for the GLMM experiment.

Calculates the achieved power for the planned GLMM given the sample size
from the filtered dataset.
"""
import os
import sys
import json
import argparse
import math
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from statsmodels.stats.power import FTestAnovaPower

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Paths

# Constants for the analysis
ALPHA = 0.05
EFFECT_SIZE = 0.15  # Cohen's f² target
GROUPS = 2  # Monolithic vs Dual-track

def load_filtered_tasks(file_path: str) -> pd.DataFrame:
    """
    Load the filtered tasks dataset.
    
    Args:
        file_path: Path to the filtered_tasks.csv file.
        
    Returns:
        DataFrame containing the filtered tasks.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Filtered tasks file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"Filtered tasks file is empty: {file_path}")
        
    # Verify required columns exist (T013 ensures these)
    required_cols = ['task_id', 'progressive_constraints', 'constraint_count']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")
        
    return df

def calculate_achieved_power(
    n_observations: int,
    groups: int = GROUPS,
    effect_size: float = EFFECT_SIZE,
    alpha: float = ALPHA
) -> float:
    """
    Calculate the achieved power for the GLMM.
    
    Uses FTestAnovaPower (appropriate for ANOVA/GLMM with fixed effects).
    For a GLMM with 2 groups and interaction term, we approximate using
    the F-test power calculation.
    
    Args:
        n_observations: Total number of observations (tasks).
        groups: Number of groups (2 for monolithic vs dual-track).
        effect_size: Cohen's f² effect size.
        alpha: Significance level.
        
    Returns:
        Calculated power (0.0 to 1.0).
    """
    if n_observations <= groups:
        # Not enough observations for any analysis
        return 0.0
        
    # Degrees of freedom for the numerator (interaction effect)
    # For 2 groups and constraint_count as continuous, interaction df = (groups-1) * 1 = 1
    df_num = groups - 1
    
    # Degrees of freedom for the denominator
    df_denom = n_observations - groups - 1  # Adjust for intercept and other terms
    
    if df_denom <= 0:
        return 0.0
        
    # Use statsmodels FTestAnovaPower
    power_analyzer = FTestAnovaPower()
    
    try:
        power = power_analyzer.solve_power(
            effect_size=effect_size,
            nobs1=n_observations,
            alpha=alpha,
            power=None,
            ratio=1.0  # Equal group sizes assumed
        )
        return float(power) if power is not None else 0.0
    except Exception:
        # If calculation fails, return 0.0
        return 0.0

def run_power_analysis(
    input_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run the power analysis and generate the report.
    
    Args:
        input_path: Path to the filtered_tasks.csv file.
        output_path: Path to write the power_report.json file.
        
    Returns:
        Dictionary containing the power analysis results.
    """
    # Load the filtered tasks
    df = load_filtered_tasks(input_path)
    
    # Get the sample size
    n_observations = len(df)
    
    # Calculate achieved power
    calculated_power = calculate_achieved_power(
        n_observations=n_observations,
        groups=GROUPS,
        effect_size=EFFECT_SIZE,
        alpha=ALPHA
    )
    
    # Prepare the report
    report = {
        "calculated_power": calculated_power,
        "effect_size": EFFECT_SIZE,
        "sample_size": n_observations,
        "groups": GROUPS,
        "alpha": ALPHA,
        "notes": "Power calculated for GLMM with 2 groups (monolithic vs dual-track) and effect size f²=0.15"
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write the report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Main entry point for the power analysis script."""
    parser = argparse.ArgumentParser(
        description="Perform power analysis on the filtered dataset for GLMM experiment."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/filtered_tasks.csv",
        help="Path to the filtered tasks CSV file (default: data/processed/filtered_tasks.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/power_report.json",
        help="Path to write the power report JSON file (default: data/processed/power_report.json)"
    )
    
    args = parser.parse_args()
    
    print(f"Loading filtered tasks from {args.input}...")
    
    try:
        report = run_power_analysis(args.input, args.output)
        
        print(f"Power analysis complete!")
        print(f"  Sample size: {report['sample_size']}")
        print(f"  Calculated power: {report['calculated_power']:.4f}")
        print(f"  Effect size: {report['effect_size']}")
        print(f"  Groups: {report['groups']}")
        print(f"Report written to: {args.output}")
        
        # Log the result
        print(f"Power analysis result: power={report['calculated_power']:.4f}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during power analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()