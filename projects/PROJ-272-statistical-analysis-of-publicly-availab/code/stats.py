import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_feature_matrix(input_path: str) -> pd.DataFrame:
    """
    Load the feature matrix from a CSV file.
    
    Args:
        input_path: Path to the CSV file containing features.
        
    Returns:
        DataFrame with feature data.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Feature matrix file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded feature matrix with {len(df)} records and {len(df.columns)} columns")
    return df

def prepare_group_data(df: pd.DataFrame, label_col: str = 'label') -> Dict[str, np.ndarray]:
    """
    Prepare data grouped by the label column for statistical testing.
    
    Args:
        df: DataFrame containing features and labels.
        label_col: Name of the column containing group labels.
        
    Returns:
        Dictionary mapping group labels to arrays of feature values.
    """
    groups = {}
    for label in df[label_col].unique():
        if pd.isna(label):
            continue
        # Select only numeric columns for statistical testing
        numeric_data = df[df[label_col] == label].select_dtypes(include=[np.number])
        if not numeric_data.empty:
            groups[str(label)] = numeric_data.values
        else:
            logger.warning(f"No numeric data found for group: {label}")
    
    return groups

def run_mann_whitney_u(group1_data: np.ndarray, group2_data: np.ndarray, 
                       feature_indices: Optional[List[int]] = None) -> Dict[str, np.ndarray]:
    """
    Run Mann-Whitney U test between two groups for specified features.
    
    Args:
        group1_data: 2D array of feature values for group 1.
        group2_data: 2D array of feature values for group 2.
        feature_indices: List of column indices to test. If None, test all columns.
        
    Returns:
        Dictionary with 'statistics' and 'p_values' arrays.
    """
    if feature_indices is None:
        feature_indices = list(range(group1_data.shape[1]))
    
    statistics = []
    p_values = []
    
    for idx in feature_indices:
        col1 = group1_data[:, idx]
        col2 = group2_data[:, idx]
        
        # Handle cases with insufficient data for testing
        if len(col1) < 2 or len(col2) < 2:
            statistics.append(np.nan)
            p_values.append(np.nan)
            continue
        
        # Remove NaN values
        col1 = col1[~np.isnan(col1)]
        col2 = col2[~np.isnan(col2)]
        
        if len(col1) < 2 or len(col2) < 2:
            statistics.append(np.nan)
            p_values.append(np.nan)
            continue
        
        u_stat, p_val = stats.mannwhitneyu(col1, col2, alternative='two-sided')
        statistics.append(u_stat)
        p_values.append(p_val)
    
    return {
        'statistics': np.array(statistics),
        'p_values': np.array(p_values)
    }

def calculate_cohens_d(group1_data: np.ndarray, group2_data: np.ndarray,
                       feature_indices: Optional[List[int]] = None) -> np.ndarray:
    """
    Calculate Cohen's d effect size between two groups for specified features.
    
    Args:
        group1_data: 2D array of feature values for group 1.
        group2_data: 2D array of feature values for group 2.
        feature_indices: List of column indices to calculate effect size for.
        
    Returns:
        Array of Cohen's d values.
    """
    if feature_indices is None:
        feature_indices = list(range(group1_data.shape[1]))
    
    d_values = []
    
    for idx in feature_indices:
        col1 = group1_data[:, idx]
        col2 = group2_data[:, idx]
        
        # Remove NaN values
        col1 = col1[~np.isnan(col1)]
        col2 = col2[~np.isnan(col2)]
        
        if len(col1) < 2 or len(col2) < 2:
            d_values.append(np.nan)
            continue
        
        mean1 = np.mean(col1)
        mean2 = np.mean(col2)
        std1 = np.std(col1, ddof=1)
        std2 = np.std(col2, ddof=1)
        
        # Pooled standard deviation
        n1, n2 = len(col1), len(col2)
        if n1 + n2 - 2 == 0:
            pooled_std = 0
        else:
            pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            d_values.append(np.nan)
        else:
            d_values.append((mean1 - mean2) / pooled_std)
    
    return np.array(d_values)

def run_group_comparisons(df: pd.DataFrame, label_col: str = 'label',
                          group1: str = 'Control', group2: str = 'AD') -> Dict[str, Any]:
    """
    Run Mann-Whitney U tests between two specified groups for all numeric features.
    
    Args:
        df: DataFrame with features and labels.
        label_col: Column name for group labels.
        group1: Label for the first group (reference).
        group2: Label for the second group (comparison).
        
    Returns:
        Dictionary with test results.
    """
    groups = prepare_group_data(df, label_col)
    
    if group1 not in groups or group2 not in groups:
        raise ValueError(f"Groups '{group1}' or '{group2}' not found in data. "
                       f"Available groups: {list(groups.keys())}")
    
    group1_data = groups[group1]
    group2_data = groups[group2]
    
    # Run Mann-Whitney U test
    mw_results = run_mann_whitney_u(group1_data, group2_data)
    
    # Calculate Cohen's d
    cohens_d = calculate_cohens_d(group1_data, group2_data)
    
    # Get feature names
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    return {
        'group1': group1,
        'group2': group2,
        'feature_names': numeric_cols,
        'mann_whitney_statistics': mw_results['statistics'].tolist(),
        'raw_p_values': mw_results['p_values'].tolist(),
        'cohens_d': cohens_d.tolist(),
        'sample_sizes': {
            group1: len(group1_data),
            group2: len(group2_data)
        }
    }

def apply_bonferroni_correction(p_values: List[float], num_tests: Optional[int] = None) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        num_tests: Number of tests performed. If None, uses len(p_values).
        
    Returns:
        List of adjusted p-values.
    """
    if num_tests is None:
        num_tests = len(p_values)
    
    if num_tests == 0:
        return []
    
    adjusted = [min(p * num_tests, 1.0) for p in p_values]
    return adjusted

def check_sample_sizes(df: pd.DataFrame, label_col: str = 'label', 
                       min_size: int = 10) -> Dict[str, Any]:
    """
    Check if group sizes meet the minimum threshold.
    
    Args:
        df: DataFrame with labels.
        label_col: Column name for group labels.
        min_size: Minimum required sample size per group.
        
    Returns:
        Dictionary with sample size information and power flag.
    """
    group_counts = df[label_col].value_counts().to_dict()
    low_power = any(count < min_size for count in group_counts.values())
    
    return {
        'group_counts': group_counts,
        'min_size': min_size,
        'low_power': low_power
    }

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical results to a JSON file.
    
    Args:
        results: Dictionary containing statistical metrics.
        output_path: Path to the output JSON file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved statistical results to {output_path}")

def main():
    """
    Main function to run statistical analysis on feature data.
    
    This function:
    1. Loads the feature matrix from the input CSV.
    2. Performs Mann-Whitney U tests between Control and AD groups.
    3. Applies Bonferroni correction to p-values.
    4. Calculates Cohen's d effect sizes.
    5. Saves results to the output JSON file.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis on feature data')
    parser.add_argument('--input', type=str, required=True, 
                      help='Path to input feature CSV file')
    parser.add_argument('--output', type=str, required=True, 
                      help='Path to output statistical metrics JSON file')
    parser.add_argument('--group1', type=str, default='Control',
                      help='Label for the first group')
    parser.add_argument('--group2', type=str, default='AD',
                      help='Label for the second group')
    parser.add_argument('--log-level', type=str, default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                      help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load feature data
        logger.info(f"Loading feature data from {args.input}")
        df = load_feature_matrix(args.input)
        
        # Check sample sizes
        sample_info = check_sample_sizes(df, label_col='label')
        if sample_info['low_power']:
            logger.warning(f"Low power detected: {sample_info['group_counts']}")
        
        # Run group comparisons
        logger.info(f"Running Mann-Whitney U test between {args.group1} and {args.group2}")
        comparison_results = run_group_comparisons(df, label_col='label', 
                                                  group1=args.group1, group2=args.group2)
        
        # Apply Bonferroni correction
        raw_p_values = comparison_results['raw_p_values']
        num_tests = len(raw_p_values)
        adjusted_p_values = apply_bonferroni_correction(raw_p_values, num_tests)
        
        # Prepare final results
        final_results = {
            'comparison': f"{args.group1}_vs_{args.group2}",
            'feature_names': comparison_results['feature_names'],
            'raw_p_values': raw_p_values,
            'adjusted_p_values': adjusted_p_values,
            'bonferroni_correction_factor': num_tests,
            'cohens_d': comparison_results['cohens_d'],
            'sample_sizes': comparison_results['sample_sizes'],
            'power_flag': 'low_power' if sample_info['low_power'] else 'adequate_power'
        }
        
        # Add significance flags
        final_results['significant_raw'] = [p < 0.05 for p in raw_p_values]
        final_results['significant_adjusted'] = [p < 0.05 for p in adjusted_p_values]
        
        # Save results
        save_results(final_results, args.output)
        
        logger.info("Statistical analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during statistical analysis: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    main()
