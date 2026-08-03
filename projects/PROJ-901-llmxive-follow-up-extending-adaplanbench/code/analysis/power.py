import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
from statsmodels.stats.power import FTestAnovaPower
from statsmodels.stats.power import tt_ind_solve_power

# Custom exception for power analysis
class PowerInsufficientError(Exception):
    """Raised when the achieved power is below the required threshold (0.80)."""
    pass

# Constants for power analysis
ALPHA = 0.05
EFFECT_SIZE_F2 = 0.15  # Cohen's f² target
GROUPS = 2             # Monolithic vs Dual-Track
TARGET_POWER = 0.80

def load_filtered_tasks(input_path: str) -> pd.DataFrame:
    """
    Load the filtered tasks dataset from the specified CSV path.
    
    Args:
        input_path: Path to the filtered_tasks.csv file.
        
    Returns:
        pandas DataFrame containing the filtered tasks.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Filtered tasks file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = ['task_id', 'constraint_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
        
    return df

def calculate_achieved_power(n_observations: int, groups: int = GROUPS, 
                             effect_size: float = EFFECT_SIZE_F2, 
                             alpha: float = ALPHA) -> float:
    """
    Calculate the achieved statistical power for a GLMM (approximated as ANOVA)
    given the sample size, number of groups, effect size, and alpha.
    
    For a GLMM with 2 groups (monolithic vs dual-track) and a continuous 
    predictor (constraint_count), we approximate using F-test power for ANOVA.
    
    Args:
        n_observations: Total number of observations (tasks).
        groups: Number of groups (default 2).
        effect_size: Cohen's f² effect size (default 0.15).
        alpha: Significance level (default 0.05).
        
    Returns:
        Calculated power value (float between 0 and 1).
    """
    if n_observations <= 0:
        return 0.0
        
    if groups < 2:
        return 0.0
        
    # Use FTestAnovaPower for ANOVA-like power calculation
    # This approximates the power for testing the fixed effects in a GLMM
    power_analyzer = FTestAnovaPower()
    
    # Calculate power: solve for power given nobs, effect_size, alpha, k_groups
    # Note: nobs in FTestAnovaPower is total sample size
    try:
        power = power_analyzer.power(
            effect_size=effect_size,
            nobs1=n_observations,
            alpha=alpha,
            k_groups=groups
        )
        return float(power)
    except Exception as e:
        # Fallback: if calculation fails, return 0.0
        print(f"Warning: Power calculation failed: {e}")
        return 0.0

def run_power_analysis(input_path: str, output_path: str) -> dict:
    """
    Run the power analysis on the filtered dataset and generate a report.
    
    Args:
        input_path: Path to the filtered_tasks.csv file.
        output_path: Path where the power_report.json will be written.
        
    Returns:
        Dictionary containing the power analysis results.
        
    Raises:
        FileNotFoundError: If input file doesn't exist.
        PowerInsufficientError: If calculated power is below 0.80.
    """
    # Load data
    df = load_filtered_tasks(input_path)
    sample_size = len(df)
    
    print(f"Loaded {sample_size} tasks from {input_path}")
    
    # Calculate achieved power
    calculated_power = calculate_achieved_power(
        n_observations=sample_size,
        groups=GROUPS,
        effect_size=EFFECT_SIZE_F2,
        alpha=ALPHA
    )
    
    print(f"Calculated power: {calculated_power:.4f}")
    print(f"Target power: {TARGET_POWER}")
    print(f"Sample size: {sample_size}")
    
    # Determine sufficiency
    sufficient = calculated_power >= TARGET_POWER
    
    # Create report
    report = {
        "calculated_power": calculated_power,
        "effect_size": EFFECT_SIZE_F2,
        "sample_size": sample_size,
        "groups": GROUPS,
        "sufficient": sufficient,
        "alpha": ALPHA,
        "target_power": TARGET_POWER
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write report to JSON
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Power report written to {output_path}")
    
    # If power is insufficient, raise exception to halt execution (FR-011)
    if not sufficient:
        raise PowerInsufficientError(
            f"Power analysis failed: calculated power ({calculated_power:.4f}) "
            f"is below threshold ({TARGET_POWER}). Sample size ({sample_size}) "
            f"may be insufficient for the specified effect size ({EFFECT_SIZE_F2})."
        )
    
    return report

def main():
    """Main entry point for the power analysis script."""
    parser = argparse.ArgumentParser(
        description='Perform power analysis on filtered AdaPlanBench subset.'
    )
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/processed/filtered_tasks.csv',
        help='Path to the filtered tasks CSV file (default: data/processed/filtered_tasks.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/power_report.json',
        help='Path to write the power report JSON (default: data/processed/power_report.json)'
    )
    
    args = parser.parse_args()
    
    print(f"Running power analysis...")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    
    try:
        report = run_power_analysis(args.input, args.output)
        print("Power analysis completed successfully.")
        print(f"Power sufficient: {report['sufficient']}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except PowerInsufficientError as e:
        print(f"Power Insufficient Error: {e}")
        # Re-raise to ensure the pipeline halts as per FR-011
        raise
    except Exception as e:
        print(f"Unexpected error during power analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
