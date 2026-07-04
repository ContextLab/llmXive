"""
Stratified statistical analysis module for US3.

Computes Spearman correlation coefficients per category,
excluding groups with fewer than 30 samples.
"""

import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 30

def load_dependencies_data(file_path: str) -> pd.DataFrame:
    """
    Load the processed dependencies data from CSV.
    
    Args:
        file_path: Path to the CSV file (e.g., data/processed/dependencies_raw.csv)
        
    Returns:
        DataFrame containing dependency data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def filter_valid_samples(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows with missing data required for correlation.
    
    Keeps rows where:
    - age_in_days is not null
    - vulnerability_count is not null
    - category is not null
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    required_cols = ['age_in_days', 'vulnerability_count', 'category']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Drop rows with null values in required columns
    filtered = df.dropna(subset=required_cols)
    
    # Convert to numeric, coercing errors to NaN
    filtered['age_in_days'] = pd.to_numeric(filtered['age_in_days'], errors='coerce')
    filtered['vulnerability_count'] = pd.to_numeric(filtered['vulnerability_count'], errors='coerce')
    
    # Drop any remaining NaNs
    filtered = filtered.dropna(subset=required_cols)
    
    logger.info(f"Filtered to {len(filtered)} valid samples for correlation")
    return filtered

def compute_stratified_correlations(df: pd.DataFrame, category_col: str = 'category') -> Dict[str, Any]:
    """
    Compute Spearman correlation per category, excluding groups with N < 30.
    
    Args:
        df: DataFrame with 'age_in_days', 'vulnerability_count', and category column
        category_col: Name of the category column
        
    Returns:
        Dictionary containing:
        - 'by_category': Dict of {category: {'rho': float, 'pvalue': float, 'n': int}}
        - 'excluded_categories': List of categories with N < 30
        - 'overall': Overall correlation for the full dataset
    """
    if category_col not in df.columns:
        raise ValueError(f"Category column '{category_col}' not found in data")
    
    # Get overall correlation first
    overall_rho, overall_pval = spearmanr(df['age_in_days'], df['vulnerability_count'])
    
    results = {
        'by_category': {},
        'excluded_categories': [],
        'overall': {
            'rho': float(overall_rho),
            'pvalue': float(overall_pval),
            'n': int(len(df))
        }
    }
    
    # Group by category and compute correlations
    categories = df[category_col].unique()
    
    for category in categories:
        cat_mask = df[category_col] == category
        cat_df = df[cat_mask]
        n = len(cat_df)
        
        if n < MIN_SAMPLE_SIZE:
            results['excluded_categories'].append({
                'category': category,
                'n': n,
                'reason': f'Sample size ({n}) below threshold ({MIN_SAMPLE_SIZE})'
            })
            logger.info(f"Excluded category '{category}': N={n} < {MIN_SAMPLE_SIZE}")
            continue
        
        try:
            rho, pval = spearmanr(cat_df['age_in_days'], cat_df['vulnerability_count'])
            results['by_category'][category] = {
                'rho': float(rho),
                'pvalue': float(pval),
                'n': n
            }
            logger.info(f"Category '{category}': rho={rho:.4f}, p={pval:.4f}, n={n}")
        except Exception as e:
            logger.warning(f"Failed to compute correlation for category '{category}': {e}")
            results['excluded_categories'].append({
                'category': category,
                'n': n,
                'reason': f'Computation error: {str(e)}'
            })
    
    return results

def run_stratified_analysis(input_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full stratified correlation analysis pipeline.
    
    Args:
        input_path: Path to input CSV file
        output_path: Optional path to write results JSON. If None, results are not written.
        
    Returns:
        Dictionary with analysis results
    """
    # Load and filter data
    df = load_dependencies_data(input_path)
    df_clean = filter_valid_samples(df)
    
    # Compute stratified correlations
    results = compute_stratified_correlations(df_clean)
    
    # Add summary statistics
    results['summary'] = {
        'total_categories_analyzed': len(results['by_category']),
        'total_categories_excluded': len(results['excluded_categories']),
        'min_sample_threshold': MIN_SAMPLE_SIZE,
        'input_file': input_path
    }
    
    # Write to file if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results written to {output_path}")
    
    return results

def main():
    """Main entry point for stratified analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run stratified correlation analysis')
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/processed/dependencies_raw.csv',
        help='Input CSV file path'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/results_stratified.json',
        help='Output JSON file path'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    results = run_stratified_analysis(args.input, args.output)
    
    print(f"Analysis complete:")
    print(f"  Categories analyzed: {results['summary']['total_categories_analyzed']}")
    print(f"  Categories excluded: {results['summary']['total_categories_excluded']}")
    print(f"  Overall correlation: rho={results['overall']['rho']:.4f}, p={results['overall']['pvalue']:.4f}")
    
    return results

if __name__ == '__main__':
    main()