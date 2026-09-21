"""
Statistical power calculation module for T021a.

Calculates statistical power for the correlation analysis against a target of >= 0.8.
Reads from dependencies_raw.csv (produced by T018) and outputs power_analysis.json.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from scipy.stats import norm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_INPUT_PATH = "data/processed/dependencies_raw.csv"
DEFAULT_OUTPUT_PATH = "data/processed/power_analysis.json"
TARGET_POWER = 0.8
DEFAULT_ALPHA = 0.05
DEFAULT_EFFECT_SIZE = 0.3  # Medium effect size (Cohen's guidelines for correlation)

def load_dependencies_data(input_path: str) -> pd.DataFrame:
    """
    Load the dependencies dataset from CSV.
    
    Args:
        input_path: Path to the dependencies_raw.csv file.
        
    Returns:
        DataFrame containing dependency data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or lacks required columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['age_in_days', 'vulnerability_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def calculate_effect_size(df: pd.DataFrame, col_x: str = 'age_in_days', col_y: str = 'vulnerability_count') -> float:
    """
    Calculate the effect size (Pearson correlation coefficient) from the data.
    
    This serves as the observed effect size for power calculation.
    
    Args:
        df: DataFrame with the data.
        col_x: Name of the independent variable column.
        col_y: Name of the dependent variable column.
        
    Returns:
        float: The calculated correlation coefficient (r).
    """
    # Drop rows with missing values for the calculation
    valid_data = df[[col_x, col_y]].dropna()
    
    if len(valid_data) < 2:
        logger.warning("Insufficient valid data points for effect size calculation.")
        return 0.0
    
    # Calculate Pearson correlation as the effect size estimate
    correlation = valid_data[col_x].corr(valid_data[col_y])
    
    # Handle NaN or infinite values
    if pd.isna(correlation) or np.isinf(correlation):
        logger.warning("Correlation calculation resulted in NaN or Inf, defaulting to 0.0")
        return 0.0
        
    return float(correlation)

def calculate_power(effect_size: float, sample_size: int, alpha: float = 0.05) -> float:
    """
    Calculate the statistical power for a correlation test.
    
    Uses the standard approximation for power in correlation tests:
    Power = 1 - beta, where beta is the probability of Type II error.
    
    The calculation uses the Fisher z-transformation approach:
    z_r = 0.5 * ln((1+r)/(1-r))
    SE = 1 / sqrt(n - 3)
    z_beta = |z_r| * sqrt(n - 3) - z_(1-alpha/2)
    Power = Phi(z_beta)
    
    Args:
        effect_size: The correlation coefficient (r).
        sample_size: Number of observations (n).
        alpha: Significance level (default 0.05).
        
    Returns:
        float: The calculated statistical power (0 to 1).
    """
    if sample_size < 3:
        logger.warning("Sample size too small for power calculation.")
        return 0.0
        
    if abs(effect_size) >= 1.0:
        # Perfect correlation implies power = 1.0 (or undefined, but practically 1)
        return 1.0
    
    # Fisher z-transformation
    z_r = 0.5 * np.log((1 + effect_size) / (1 - effect_size))
    
    # Standard error of z_r
    se = 1.0 / np.sqrt(sample_size - 3)
    
    # Critical z-value for two-tailed test
    z_crit = norm.ppf(1 - alpha / 2)
    
    # Calculate z_beta (non-centrality parameter adjusted)
    # For power calculation, we look at the distribution under the alternative hypothesis
    z_beta = abs(z_r) / se - z_crit
    
    # Power is the probability that we reject the null hypothesis when the alternative is true
    power = norm.cdf(z_beta)
    
    return float(power)

def run_power_analysis(input_path: str = DEFAULT_INPUT_PATH, 
                       output_path: str = DEFAULT_OUTPUT_PATH,
                       alpha: float = DEFAULT_ALPHA,
                       target_power: float = TARGET_POWER) -> Dict[str, Any]:
    """
    Run the full power analysis pipeline.
    
    1. Loads data from input_path.
    2. Calculates effect size from the data.
    3. Calculates statistical power.
    4. Writes results to output_path.
    
    Args:
        input_path: Path to the input CSV file.
        output_path: Path to the output JSON file.
        alpha: Significance level.
        target_power: The target power threshold to compare against.
        
    Returns:
        Dict containing the analysis results.
    """
    logger.info(f"Starting power analysis. Input: {input_path}, Output: {output_path}")
    
    # Load data
    df = load_dependencies_data(input_path)
    sample_size = len(df)
    
    # Calculate effect size from actual data
    effect_size = calculate_effect_size(df)
    logger.info(f"Calculated effect size (r): {effect_size:.4f}")
    
    # Calculate power
    actual_power = calculate_power(effect_size, sample_size, alpha)
    logger.info(f"Calculated statistical power: {actual_power:.4f}")
    
    # Determine if target is met
    target_met = actual_power >= target_power
    logger.info(f"Target power ({target_power}) met: {target_met}")
    
    # Prepare results
    results = {
        'effect_size': round(effect_size, 6),
        'alpha': alpha,
        'sample_size': sample_size,
        'actual_power': round(actual_power, 6),
        'target_power': target_power,
        'target_met': target_met,
        'methodology_notes': (
            f"Effect size calculated as Pearson correlation between 'age_in_days' and 'vulnerability_count' "
            f"from {sample_size} samples. Power calculated using Fisher z-transformation for two-tailed test "
            f"at alpha={alpha}. Target power threshold: {target_power}."
        )
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Power analysis results written to {output_path}")
    return results

def main():
    """Entry point for the power analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Calculate statistical power for correlation analysis.')
    parser.add_argument('--input', type=str, default=DEFAULT_INPUT_PATH, 
                        help=f'Path to input CSV (default: {DEFAULT_INPUT_PATH})')
    parser.add_argument('--output', type=str, default=DEFAULT_OUTPUT_PATH,
                        help=f'Path to output JSON (default: {DEFAULT_OUTPUT_PATH})')
    parser.add_argument('--alpha', type=float, default=DEFAULT_ALPHA,
                        help=f'Significance level (default: {DEFAULT_ALPHA})')
    
    args = parser.parse_args()
    
    try:
        results = run_power_analysis(
            input_path=args.input,
            output_path=args.output,
            alpha=args.alpha
        )
        print(f"Analysis complete. Power: {results['actual_power']:.4f}, Target Met: {results['target_met']}")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during power analysis: {e}")
        raise

if __name__ == "__main__":
    main()
