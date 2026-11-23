import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path
import pandas as pd
from statsmodels.stats.power import TTestIndPower

# Import seed enforcement from helpers
from utils.helpers import set_reproducibility_seed, get_project_root

# Set seed at the very start of the script
set_reproducibility_seed()

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_submissions_csv_path() -> Path:
    """Returns the path to the submissions CSV file."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path() -> Path:
    """Returns the path to the cleaned CSV file."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_output_path() -> Path:
    """Returns the path to the power analysis report JSON file."""
    return get_project_root() / "data" / "processed" / "power_analysis_report.json"

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Loads cleaned data from the specified path."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def calculate_power_z_test(effect_size: float, nobs: int, alpha: float = 0.05) -> float:
    """
    Calculates statistical power for a two-sample t-test (independent samples).
    
    Args:
        effect_size: Cohen's d effect size.
        nobs: Number of observations in one group (assuming balanced design).
        alpha: Significance level.
    
    Returns:
        Statistical power (probability of rejecting null hypothesis when false).
    """
    power_calc = TTestIndPower()
    # For repeated measures, we approximate with independent samples power calculation
    # using the total N as the effective sample size per group for a conservative estimate
    # or split N for the two conditions being compared.
    # Here we use total N for a rough estimate of power to detect the effect.
    power = power_calc.power(effect_size=effect_size, nobs1=nobs, alpha=alpha)
    return float(power)

def run_power_analysis(df: pd.DataFrame, assumed_effect_size: float = 0.5) -> dict:
    """
    Runs power analysis based on observed data.
    
    Args:
        df: Cleaned DataFrame containing the survey data.
        assumed_effect_size: Default moderate effect size (Cohen's d).
    
    Returns:
        Dictionary containing power analysis results.
    """
    # Calculate sample size (N)
    n = len(df)
    
    if n == 0:
        raise ValueError("Sample size is zero. Cannot perform power analysis.")
    
    # Calculate power using the assumed effect size and observed sample size
    power = calculate_power_z_test(assumed_effect_size, n)
    
    results = {
        "sample_size": n,
        "assumed_effect_size": assumed_effect_size,
        "power": power,
        "alpha": 0.05,
        "adequate_power": power >= 0.80
    }
    
    return results

def main():
    """Main entry point for the power analysis script."""
    parser = argparse.ArgumentParser(description='Run post-collection power analysis')
    parser.add_argument('--input', type=str, help='Input CSV file path (cleaned data)')
    parser.add_argument('--output', type=str, help='Output JSON file path')
    args = parser.parse_args()
    
    # Determine input path: prefer command line, else cleaned data, else submissions (fallback)
    if args.input:
        input_path = Path(args.input)
    else:
        cleaned_path = get_cleaned_csv_path()
        submissions_path = get_submissions_csv_path()
        
        if cleaned_path.exists():
            input_path = cleaned_path
        elif submissions_path.exists():
            input_path = submissions_path
        else:
            print("Error: No input data found. Expected 'data/processed/clean_data.csv' or 'data/raw/submissions.csv'.")
            sys.exit(1)
    
    output_path = Path(args.output) if args.output else get_output_path()
    
    try:
        # Load data
        print(f"Loading data from {input_path}...")
        df = load_cleaned_data(input_path)
        
        # Run power analysis
        results = run_power_analysis(df)
        
        # Print warning if power is low
        if not results['adequate_power']:
            print(f"Warning: Power ({results['power']:.2f}) is below 0.80. Consider increasing sample size.")
        else:
            print(f"Power ({results['power']:.2f}) is adequate (>= 0.80).")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"Power analysis report saved to {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()