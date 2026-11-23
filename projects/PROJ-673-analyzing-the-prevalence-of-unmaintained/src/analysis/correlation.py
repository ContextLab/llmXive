"""
Statistical Analysis Module for Spearman Correlation
Implements FR-006: Calculate Spearman rho and p-value between dependency age and vulnerability density.
"""
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_dependencies_data(csv_path: str) -> pd.DataFrame:
    """
    Load the processed dependencies data from CSV.
    
    Args:
        csv_path: Path to the CSV file containing dependency data.
        
    Returns:
        DataFrame with columns: age_in_days, vulnerability_count
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}. "
                                "Ensure T018 has run and produced data/processed/dependencies_raw.csv")
    
    df = pd.read_csv(csv_path)
    
    required_cols = ['age_in_days', 'vulnerability_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {csv_path}: {missing_cols}")
    
    # Filter out rows where age_in_days is null (NaN) as per FR-010
    # These rows should be excluded from age-based correlation but 
    # would have been included in vulnerability counts if calculated separately.
    initial_count = len(df)
    df = df.dropna(subset=['age_in_days'])
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows with null age_in_days for correlation analysis.")
    
    # Ensure numeric types
    df['age_in_days'] = pd.to_numeric(df['age_in_days'], errors='coerce')
    df['vulnerability_count'] = pd.to_numeric(df['vulnerability_count'], errors='coerce')
    
    # Drop any remaining NaNs after conversion
    df = df.dropna(subset=['age_in_days', 'vulnerability_count'])
    
    logger.info(f"Loaded {len(df)} valid samples for correlation analysis.")
    return df

def calculate_spearman_correlation(df: pd.DataFrame) -> Tuple[float, float, Dict[str, Any]]:
    """
    Calculate Spearman rank correlation between dependency age and vulnerability count.
    
    Args:
        df: DataFrame with 'age_in_days' and 'vulnerability_count' columns.
        
    Returns:
        Tuple of (correlation_coefficient, p_value, stats_dict)
    """
    if len(df) < 2:
        raise ValueError("Insufficient data points for correlation analysis (n < 2).")
    
    age = df['age_in_days'].values
    vuln = df['vulnerability_count'].values
    
    # Check for constant values which cause correlation to be undefined
    if np.std(age) == 0 or np.std(vuln) == 0:
        logger.warning("Constant values detected in one or both variables. Correlation undefined.")
        return np.nan, np.nan, {
            'n': len(df),
            'std_age': np.std(age),
            'std_vuln': np.std(vuln),
            'mean_age': np.mean(age),
            'mean_vuln': np.mean(vuln)
        }
    
    try:
        rho, p_value = spearmanr(age, vuln)
    except Exception as e:
        logger.error(f"Error calculating Spearman correlation: {e}")
        raise
    
    stats = {
        'n': len(df),
        'mean_age': float(np.mean(age)),
        'std_age': float(np.std(age)),
        'mean_vuln': float(np.mean(vuln)),
        'std_vuln': float(np.std(vuln)),
        'min_age': float(np.min(age)),
        'max_age': float(np.max(age)),
        'min_vuln': float(np.min(vuln)),
        'max_vuln': float(np.max(vuln))
    }
    
    return float(rho), float(p_value), stats

def run_correlation_analysis(input_csv: str, output_json: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        input_csv: Path to the input CSV file (dependencies_raw.csv).
        output_json: Optional path to save results as JSON.
        
    Returns:
        Dictionary containing correlation results and statistics.
    """
    logger.info(f"Starting correlation analysis with input: {input_csv}")
    
    # Load data
    df = load_dependencies_data(input_csv)
    
    # Calculate correlation
    rho, p_value, stats = calculate_spearman_correlation(df)
    
    result = {
        'correlation_coefficient': rho,
        'p_value': p_value,
        'is_significant': p_value < 0.05 if p_value is not None else None,
        'sample_size': stats['n'],
        'statistics': stats
    }
    
    logger.info(f"Correlation coefficient (rho): {rho:.4f}")
    logger.info(f"P-value: {p_value:.6f}")
    logger.info(f"Statistical significance (p < 0.05): {result['is_significant']}")
    
    # Save to JSON if path provided
    if output_json:
        output_path = Path(output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results saved to {output_json}")
    
    return result

def main():
    """Entry point for running correlation analysis via CLI."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Calculate Spearman correlation between dependency age and vulnerability count.')
    parser.add_argument('--input', '-i', type=str, default='data/processed/dependencies_raw.csv',
                      help='Path to input CSV file (default: data/processed/dependencies_raw.csv)')
    parser.add_argument('--output', '-o', type=str, default='data/processed/results_correlation.json',
                      help='Path to output JSON file (default: data/processed/results_correlation.json)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING)
    
    try:
        result = run_correlation_analysis(args.input, args.output)
        print(f"\nAnalysis Complete:")
        print(f"  Correlation (rho): {result['correlation_coefficient']:.4f}")
        print(f"  P-value: {result['p_value']:.6f}")
        print(f"  Significant (p<0.05): {result['is_significant']}")
        print(f"  Sample Size: {result['sample_size']}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
