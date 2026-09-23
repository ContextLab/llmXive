import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy.stats import spearmanr
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dependencies_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the dependencies data from the processed CSV file.
    Defaults to data/processed/dependencies_raw.csv if no path is provided.
    """
    if input_path is None:
        input_path = "data/processed/dependencies_raw.csv"
    
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(path)
    
    # Ensure required columns exist
    required_cols = ['age_in_days', 'vulnerability_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter out rows with missing data for correlation
    # age_in_days might be null if release_date was missing (per FR-010)
    # vulnerability_count should always be present (int)
    valid_df = df.dropna(subset=['age_in_days', 'vulnerability_count'])
    
    logger.info(f"Loaded {len(df)} rows, {len(valid_df)} valid for correlation analysis")
    return valid_df

def calculate_spearman_correlation(df: pd.DataFrame) -> Tuple[float, float, int]:
    """
    Calculate Spearman rank correlation between age_in_days and vulnerability_count.
    
    Returns:
        Tuple of (correlation_coefficient, p_value, sample_size)
    """
    if len(df) < 2:
        logger.warning("Insufficient data for correlation (need at least 2 samples)")
        return 0.0, 1.0, len(df)
    
    age = df['age_in_days'].values
    vulns = df['vulnerability_count'].values
    
    # Handle case where all values are identical (constant)
    if np.std(age) == 0 or np.std(vulns) == 0:
        logger.warning("One of the variables is constant; correlation undefined")
        return 0.0, 1.0, len(df)
    
    try:
        rho, p_value = spearmanr(age, vulns)
        return float(rho), float(p_value), len(df)
    except Exception as e:
        logger.error(f"Error calculating Spearman correlation: {e}")
        raise

def run_correlation_analysis(input_path: Optional[str] = None, 
                             output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline.
    
    Args:
        input_path: Path to input CSV (default: data/processed/dependencies_raw.csv)
        output_path: Path to output JSON (default: data/processed/results_correlation.json)
    
    Returns:
        Dictionary containing correlation results
    """
    if output_path is None:
        output_path = "data/processed/results_correlation.json"
    
    # Load data
    df = load_dependencies_data(input_path)
    
    # Calculate correlation
    rho, p_value, sample_size = calculate_spearman_correlation(df)
    
    # Determine statistical significance
    is_significant = p_value < 0.05
    
    # Prepare results
    results = {
        "correlation_coefficient": rho,
        "p_value": p_value,
        "sample_size": sample_size,
        "is_statistically_significant": is_significant,
        "alpha_threshold": 0.05,
        "method": "Spearman rank correlation"
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    logger.info(f"Writing results to {output_path}")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Correlation analysis complete: rho={rho:.4f}, p={p_value:.4f}, n={sample_size}")
    return results

def main():
    """Main entry point for the correlation analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate Spearman correlation for dependency data")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/dependencies_raw.csv",
        help="Path to input CSV file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/results_correlation.json",
        help="Path to output JSON file"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_correlation_analysis(args.input, args.output)
        print(f"Analysis complete. Results written to {args.output}")
        print(f"  Correlation (rho): {results['correlation_coefficient']:.4f}")
        print(f"  P-value: {results['p_value']:.4f}")
        print(f"  Sample size: {results['sample_size']}")
        print(f"  Statistically significant (p < 0.05): {results['is_statistically_significant']}")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())