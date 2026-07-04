import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.analysis.correlation import load_dependencies_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_unmaintained_proportion(df: pd.DataFrame, threshold_days: int) -> float:
    """
    Calculate the proportion of dependencies considered 'unmaintained'
    based on a binary threshold of age_in_days.
    
    Only rows with valid age_in_days are considered.
    """
    valid_mask = df['age_in_days'].notna()
    if not valid_mask.any():
        return 0.0
    
    subset = df.loc[valid_mask, 'age_in_days']
    unmaintained = (subset >= threshold_days).sum()
    total = len(subset)
    
    return float(unmaintained / total)

def run_sensitivity_analysis(
    input_path: str,
    output_path: str,
    thresholds: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis for different 'unmaintained' thresholds.
    
    This applies thresholds ONLY to binary metrics (proportion unmaintained),
    NOT to the primary continuous correlation calculation.
    
    Args:
        input_path: Path to dependencies_raw.csv
        output_path: Path to write sensitivity_analysis.json
        thresholds: List of days to test (default: [90, 180, 365])
    
    Returns:
        Dictionary containing analysis results
    """
    if thresholds is None:
        thresholds = [90, 180, 365]
    
    logger.info(f"Loading data from {input_path}")
    df = load_dependencies_data(input_path)
    
    if df.empty:
        logger.warning("Input data is empty. Returning empty results.")
        result = {
            "thresholds_tested": thresholds,
            "total_samples": 0,
            "valid_samples": 0,
            "results": []
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result
    
    valid_mask = df['age_in_days'].notna()
    valid_count = valid_mask.sum()
    
    analysis_results = []
    
    for threshold in thresholds:
        logger.info(f"Testing threshold: {threshold} days")
        
        # Calculate binary metric: proportion unmaintained
        prop_unmaintained = calculate_unmaintained_proportion(df, threshold)
        
        # Calculate mean age for unmaintained subset
        unmaintained_mask = valid_mask & (df['age_in_days'] >= threshold)
        if unmaintained_mask.any():
            mean_age_unmaintained = float(df.loc[unmaintained_mask, 'age_in_days'].mean())
            std_age_unmaintained = float(df.loc[unmaintained_mask, 'age_in_days'].std())
            count_unmaintained = int(unmaintained_mask.sum())
        else:
            mean_age_unmaintained = None
            std_age_unmaintained = None
            count_unmaintained = 0
        
        # Calculate mean age for maintained subset
        maintained_mask = valid_mask & (df['age_in_days'] < threshold)
        if maintained_mask.any():
            mean_age_maintained = float(df.loc[maintained_mask, 'age_in_days'].mean())
        else:
            mean_age_maintained = None
        
        result_entry = {
            "threshold_days": threshold,
            "proportion_unmaintained": prop_unmaintained,
            "count_unmaintained": count_unmaintained,
            "mean_age_unmaintained": mean_age_unmaintained,
            "std_age_unmaintained": std_age_unmaintained,
            "mean_age_maintained": mean_age_maintained
        }
        analysis_results.append(result_entry)
    
    output_data = {
        "thresholds_tested": thresholds,
        "total_samples": len(df),
        "valid_samples": int(valid_count),
        "results": analysis_results
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing results to {output_path}")
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_data

def main():
    """Entry point for sensitivity analysis script."""
    # Default paths based on project structure
    input_path = "data/processed/dependencies_raw.csv"
    output_path = "data/processed/sensitivity_analysis.json"
    
    # Allow override via environment or command line if needed
    # For now, using defaults as per task specification
    
    try:
        results = run_sensitivity_analysis(input_path, output_path)
        logger.info("Sensitivity analysis completed successfully.")
        logger.info(f"Results written to {output_path}")
        
        # Print summary
        print(f"\nSensitivity Analysis Summary:")
        print(f"Total samples: {results['total_samples']}")
        print(f"Valid samples (with age_in_days): {results['valid_samples']}")
        print("\nProportion unmaintained by threshold:")
        for res in results['results']:
            print(f"  {res['threshold_days']} days: {res['proportion_unmaintained']:.4f} ({res['count_unmaintained']} packages)")
            
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()
