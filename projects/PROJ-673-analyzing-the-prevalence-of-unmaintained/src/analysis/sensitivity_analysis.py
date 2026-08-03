import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dependencies_data(file_path: str) -> pd.DataFrame:
    """
    Load the dependencies dataset from CSV.
    
    Args:
        file_path: Path to the CSV file (e.g., data/processed/dependencies_raw.csv)
        
    Returns:
        pandas DataFrame with dependency data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def calculate_unmaintained_proportion(df: pd.DataFrame, threshold_days: int, 
                                     age_column: str = 'age_in_days',
                                     category_column: str = 'category') -> Dict[str, Any]:
    """
    Calculate the proportion of unmaintained dependencies for a given threshold.
    
    A dependency is considered "unmaintained" if its age_in_days exceeds the threshold.
    Dependencies with null/NaN age_in_days are excluded from this binary calculation.
    
    Args:
        df: DataFrame containing dependency data
        threshold_days: The threshold in days (e.g., 90, 180, 365)
        age_column: Name of the column containing age in days
        category_column: Name of the column containing package categories
        
    Returns:
        Dictionary with overall proportion and per-category proportions
    """
    # Filter out rows with missing age data for this binary calculation
    valid_df = df.dropna(subset=[age_column])
    
    if len(valid_df) == 0:
        return {
            'threshold_days': threshold_days,
            'total_dependencies': 0,
            'unmaintained_count': 0,
            'unmaintained_proportion': None,
            'by_category': {}
        }
    
    # Calculate binary unmaintained flag
    valid_df = valid_df.copy()
    valid_df['is_unmaintained'] = valid_df[age_column] > threshold_days
    
    # Overall proportion
    total = len(valid_df)
    unmaintained_count = valid_df['is_unmaintained'].sum()
    proportion = unmaintained_count / total if total > 0 else 0.0
    
    # Per-category proportions
    by_category = {}
    if category_column in valid_df.columns:
        for category, group in valid_df.groupby(category_column):
            cat_total = len(group)
            cat_unmaintained = group['is_unmaintained'].sum()
            cat_proportion = cat_unmaintained / cat_total if cat_total > 0 else 0.0
            by_category[category] = {
                'total': int(cat_total),
                'unmaintained_count': int(cat_unmaintained),
                'unmaintained_proportion': float(cat_proportion)
            }
    
    return {
        'threshold_days': threshold_days,
        'total_dependencies': int(total),
        'unmaintained_count': int(unmaintained_count),
        'unmaintained_proportion': float(proportion),
        'by_category': by_category
    }

def run_sensitivity_analysis(df: pd.DataFrame, 
                            thresholds: List[int] = [90, 180, 365],
                            age_column: str = 'age_in_days',
                            category_column: str = 'category') -> Dict[str, Any]:
    """
    Run sensitivity analysis across multiple thresholds.
    
    This analysis is applied ONLY to the binary "unmaintained" classification
    and secondary metrics, NOT to the primary continuous correlation analysis.
    
    Args:
        df: DataFrame containing dependency data
        thresholds: List of threshold days to test (default: [90, 180, 365])
        age_column: Name of the age column
        category_column: Name of the category column
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    
    results = {
        'description': 'Sensitivity analysis for "unmaintained" threshold classification',
        'note': 'This analysis applies binary thresholds to age_in_days for secondary metrics only. '
                'The primary correlation analysis uses continuous age values.',
        'thresholds_tested': thresholds,
        'results_by_threshold': [],
        'summary': {}
    }
    
    for threshold in thresholds:
        threshold_result = calculate_unmaintained_proportion(
            df, threshold, age_column, category_column
        )
        results['results_by_threshold'].append(threshold_result)
        logger.info(f"Threshold {threshold} days: {threshold_result['unmaintained_proportion']:.4f} unmaintained")
    
    # Summary statistics
    proportions = [r['unmaintained_proportion'] for r in results['results_by_threshold'] 
                  if r['unmaintained_proportion'] is not None]
    
    if proportions:
        results['summary'] = {
            'min_proportion': float(min(proportions)),
            'max_proportion': float(max(proportions)),
            'mean_proportion': float(np.mean(proportions)),
            'std_proportion': float(np.std(proportions)),
            'robustness_note': 'If proportions vary significantly across thresholds, '
                              'the "unmaintained" classification is sensitive to threshold choice.'
        }
    
    return results

def main():
    """
    Main entry point for sensitivity analysis.
    
    Loads dependencies_raw.csv, runs sensitivity analysis with thresholds [90, 180, 365],
    and writes results to data/processed/sensitivity_analysis.json.
    """
    # Define paths
    input_path = Path("data/processed/dependencies_raw.csv")
    output_path = Path("data/processed/sensitivity_analysis.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting sensitivity analysis pipeline")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Load data
        df = load_dependencies_data(str(input_path))
        
        # Run sensitivity analysis
        results = run_sensitivity_analysis(
            df,
            thresholds=[90, 180, 365],
            age_column='age_in_days',
            category_column='category'
        )
        
        # Write results to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
        logger.info(f"Summary: {results['summary']}")
        
        return results
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    main()