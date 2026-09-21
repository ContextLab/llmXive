import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

def load_dependencies_data(input_path: str) -> pd.DataFrame:
    """
    Load the dependencies dataset from a CSV file.
    
    Args:
        input_path: Path to the CSV file containing dependency data.
        
    Returns:
        pandas DataFrame with the loaded data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['age_in_days', 'vulnerability_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter out rows where critical columns are NaN for correlation calculation
    # We keep rows for analysis but exclude NaNs from the correlation computation
    logger.info(f"Loaded {len(df)} rows. Filtering NaNs for correlation...")
    valid_mask = df['age_in_days'].notna() & df['vulnerability_count'].notna()
    valid_df = df[valid_mask]
    
    logger.info(f"Valid samples for correlation: {len(valid_df)} / {len(df)}")
    
    if len(valid_df) == 0:
        raise ValueError("No valid samples available for correlation (all age_in_days or vulnerability_count are NaN).")
    
    return valid_df

def calculate_spearman_correlation(df: pd.DataFrame, 
                                   x_col: str = 'age_in_days', 
                                   y_col: str = 'vulnerability_count') -> Tuple[float, float]:
    """
    Calculate the Spearman rank correlation coefficient and p-value.
    
    Args:
        df: DataFrame containing the data.
        x_col: Name of the column for the independent variable (age).
        y_col: Name of the column for the dependent variable (vulnerabilities).
        
    Returns:
        Tuple of (rho, p_value).
        
    Raises:
        ValueError: If there are fewer than 2 valid samples.
    """
    if len(df) < 2:
        raise ValueError(f"Need at least 2 samples for correlation, got {len(df)}")
    
    x = df[x_col].values
    y = df[y_col].values
    
    # scipy.stats.spearmanr handles NaNs if we filter beforehand, but double check
    # Since we filtered in load_dependencies_data, this should be safe
    rho, p_value = spearmanr(x, y)
    
    return float(rho), float(p_value)

def run_correlation_analysis(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline:
    1. Load data
    2. Calculate Spearman correlation
    3. Determine statistical significance
    4. Save results to JSON
    
    Args:
        input_path: Path to input CSV file.
        output_path: Path to output JSON file.
        
    Returns:
        Dictionary containing the analysis results.
    """
    logger.info(f"Starting correlation analysis: {input_path} -> {output_path}")
    
    df = load_dependencies_data(input_path)
    rho, p_value = calculate_spearman_correlation(df)
    
    is_significant = p_value < 0.05
    
    result = {
        "rho": rho,
        "p_value": p_value,
        "is_significant": is_significant,
        "sample_size": len(df),
        "input_file": input_path,
        "method": "Spearman Rank Correlation",
        "threshold": 0.05
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Correlation (rho): {rho:.4f}, p-value: {p_value:.4f}, Significant: {is_significant}")
    
    return result

def main():
    """Main entry point for the correlation analysis script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Calculate Spearman correlation between package age and vulnerability count.")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to input CSV file (e.g., data/processed/dependencies_raw.csv)")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to output JSON file (e.g., data/processed/results_correlation.json)")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        result = run_correlation_analysis(args.input, args.output)
        print(f"Analysis complete. Results: {result}")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()