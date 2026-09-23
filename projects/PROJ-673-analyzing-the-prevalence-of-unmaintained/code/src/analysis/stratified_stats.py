import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dependencies_data(input_path: str) -> pd.DataFrame:
    """
    Load dependencies data from a CSV file.
    
    Args:
        input_path: Path to the input CSV file
        
    Returns:
        DataFrame with dependency data
    """
    logger.info(f"Loading data from {input_path}")
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['age_in_days', 'vulnerability_count', 'category']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Handle null values for age_in_days
    df = df.dropna(subset=['age_in_days', 'vulnerability_count'])
    
    logger.info(f"Loaded {len(df)} records")
    return df

def filter_valid_groups(df: pd.DataFrame, min_size: int = 30) -> pd.DataFrame:
    """
    Filter out groups with fewer than min_size records.
    
    Args:
        df: Input DataFrame
        min_size: Minimum group size (default 30)
        
    Returns:
        DataFrame with only valid groups
    """
    category_counts = df['category'].value_counts()
    valid_categories = category_counts[category_counts >= min_size].index
    logger.info(f"Valid categories (N >= {min_size}): {list(valid_categories)}")
    return df[df['category'].isin(valid_categories)]

def compute_stratified_correlations(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    """
    Compute Spearman correlation for each category.
    
    Args:
        df: DataFrame with dependency data
        
    Returns:
        Dictionary mapping category to correlation stats
    """
    results = {}
    
    for category in df['category'].unique():
        group = df[df['category'] == category]
        
        if len(group) < 2:
            logger.warning(f"Skipping {category}: insufficient data (n={len(group)})")
            continue
        
        # Calculate Spearman correlation
        try:
            rho, p_value = spearmanr(group['age_in_days'], group['vulnerability_count'])
            
            if np.isnan(rho) or np.isnan(p_value):
                logger.warning(f"Correlation undefined for {category}")
                continue
            
            results[category] = {
                'correlation_coefficient': float(rho),
                'p_value': float(p_value),
                'sample_size': int(len(group))
            }
            logger.info(f"{category}: rho={rho:.4f}, p={p_value:.4f}, n={len(group)}")
            
        except Exception as e:
            logger.error(f"Error computing correlation for {category}: {e}")
            continue
    
    return results

def calculate_variance_across_categories(stratified_results: Dict[str, Dict[str, float]]) -> Tuple[Dict[str, float], float]:
    """
    Calculate variance of correlation coefficients across categories.
    
    Args:
        stratified_results: Dictionary of correlation results by category
        
    Returns:
        Tuple of (category_variances, overall_variance)
    """
    if not stratified_results:
        logger.warning("No stratified results to compute variance")
        return {}, 0.0
    
    # Extract correlation coefficients
    rhos = [data['correlation_coefficient'] for data in stratified_results.values()]
    
    if len(rhos) < 2:
        logger.warning("Insufficient categories to compute variance")
        return {cat: 0.0 for cat in stratified_results.keys()}, 0.0
    
    # Calculate variance for each category (using the correlation as a point estimate)
    # Note: In a more sophisticated analysis, we might use bootstrapping or confidence intervals
    # Here we compute the squared deviation from the mean as a simple variance proxy
    mean_rho = np.mean(rhos)
    category_variances = {
        cat: float((data['correlation_coefficient'] - mean_rho) ** 2)
        for cat, data in stratified_results.items()
    }
    
    # Overall variance of the correlation coefficients
    overall_variance = float(np.var(rhos, ddof=1))
    
    logger.info(f"Mean correlation: {mean_rho:.4f}")
    logger.info(f"Overall variance: {overall_variance:.4f}")
    logger.info(f"Category variances: {category_variances}")
    
    return category_variances, overall_variance

def run_stratified_analysis(
    input_path: str,
    output_path: str,
    min_group_size: int = 30
) -> Dict[str, Any]:
    """
    Run stratified analysis and save results.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output JSON
        min_group_size: Minimum group size for inclusion
        
    Returns:
        Results dictionary
    """
    # Load and filter data
    df = load_dependencies_data(input_path)
    df_valid = filter_valid_groups(df, min_group_size)
    
    if len(df_valid) == 0:
        raise ValueError("No valid groups after filtering. Check min_group_size parameter.")
    
    # Compute stratified correlations
    stratified_results = compute_stratified_correlations(df_valid)
    
    if not stratified_results:
        raise ValueError("No valid correlations computed. Check data quality.")
    
    # Calculate variance across categories
    category_variances, overall_variance = calculate_variance_across_categories(stratified_results)
    
    # Prepare output
    results = {
        'stratified_correlations': stratified_results,
        'category_variances': category_variances,
        'overall_variance': overall_variance,
        'total_valid_groups': len(stratified_results),
        'min_group_size_threshold': min_group_size
    }
    
    # Save to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return results

def append_variance_to_correlation_results(
    stratified_output_path: str,
    correlation_output_path: str
) -> None:
    """
    Append variance calculations to the main correlation results file.
    
    Args:
        stratified_output_path: Path to stratified stats output
        correlation_output_path: Path to main correlation results
    """
    # Load stratified results
    with open(stratified_output_path, 'r') as f:
        stratified_data = json.load(f)
    
    # Load existing correlation results
    if not Path(correlation_output_path).exists():
        raise FileNotFoundError(f"Correlation results file not found: {correlation_output_path}")
    
    with open(correlation_output_path, 'r') as f:
        correlation_data = json.load(f)
    
    # Append variance data
    correlation_data['category_variances'] = stratified_data['category_variances']
    correlation_data['overall_variance'] = stratified_data['overall_variance']
    
    # Save updated results
    with open(correlation_output_path, 'w') as f:
        json.dump(correlation_data, f, indent=2)
    
    logger.info(f"Appended variance data to {correlation_output_path}")

def main():
    """Main entry point for stratified stats analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stratified correlation analysis')
    parser.add_argument('--input', type=str, default='data/processed/dependencies_raw.csv',
                      help='Input CSV file path')
    parser.add_argument('--output', type=str, default='data/processed/results_stratified.json',
                      help='Output JSON file path')
    parser.add_argument('--correlation-output', type=str, 
                      default='data/processed/results_correlation.json',
                      help='Path to correlation results for variance appending')
    parser.add_argument('--min-group-size', type=int, default=30,
                      help='Minimum group size for inclusion')
    parser.add_argument('--variance', action='store_true',
                      help='Append variance calculations to correlation results')
    
    args = parser.parse_args()
    
    try:
        # Run stratified analysis
        results = run_stratified_analysis(
            input_path=args.input,
            output_path=args.output,
            min_group_size=args.min_group_size
        )
        
        # If --variance flag is set, append to correlation results
        if args.variance:
            append_variance_to_correlation_results(
                stratified_output_path=args.output,
                correlation_output_path=args.correlation_output
            )
        
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()