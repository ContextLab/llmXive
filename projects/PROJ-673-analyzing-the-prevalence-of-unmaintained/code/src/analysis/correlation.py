import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Tuple, Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def load_dependencies_data(file_path: str) -> pd.DataFrame:
    """
    Load the dependencies dataset from a CSV file.
    
    Args:
        file_path: Path to the CSV file (e.g., data/processed/dependencies_raw.csv)
        
    Returns:
        DataFrame containing dependency data
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If required columns are missing
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
        
    df = pd.read_csv(path)
    
    required_cols = ['age_in_days', 'vulnerability_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    # Filter out rows where age_in_days is NaN (missing release metadata)
    # as per FR-010: exclude dependencies with missing release metadata from age calculation
    df_clean = df.dropna(subset=['age_in_days'])
    logger.info(f"Loaded {len(df)} rows, filtered to {len(df_clean)} rows with valid age data")
    
    return df_clean

def calculate_spearman_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation between dependency age and vulnerability count.
    
    Args:
        df: DataFrame with 'age_in_days' and 'vulnerability_count' columns
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
        
    Raises:
        ValueError: If insufficient data points
    """
    if len(df) < 2:
        raise ValueError("Insufficient data points for correlation analysis (need >= 2)")
        
    x = df['age_in_days'].values
    y = df['vulnerability_count'].values
    
    # Remove any remaining NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    if np.sum(mask) < 2:
        raise ValueError("Insufficient valid data points after NaN removal")
        
    rho, p_value = spearmanr(x[mask], y[mask])
    
    logger.info(f"Spearman correlation: rho={rho:.4f}, p-value={p_value:.6f}")
    return rho, p_value

def run_correlation_analysis(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline: load data, calculate correlation,
    determine statistical significance, and save results.
    
    Args:
        data_path: Path to input CSV file
        output_path: Path to output JSON results file
        
    Returns:
        Dictionary containing analysis results
    """
    # Load data
    df = load_dependencies_data(data_path)
    
    # Calculate correlation
    rho, p_value = calculate_spearman_correlation(df)
    
    # Flag statistical significance (US-2 Acceptance 3)
    is_significant = p_value < 0.05
    
    # Prepare results
    results = {
        "correlation_coefficient": float(rho),
        "p_value": float(p_value),
        "is_statistically_significant": is_significant,
        "significance_threshold": 0.05,
        "sample_size": int(len(df)),
        "data_source": data_path
    }
    
    # Determine significance message
    if is_significant:
        significance_msg = f"Statistically significant (p < 0.05)"
    else:
        significance_msg = "Not statistically significant (p >= 0.05)"
        
    results["significance_interpretation"] = significance_msg
    logger.info(f"Significance: {significance_msg}")
    
    # Save results to JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")
    return results