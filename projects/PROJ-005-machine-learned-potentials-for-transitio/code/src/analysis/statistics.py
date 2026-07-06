"""
Statistical analysis module for ML potential error distributions.

Implements unpaired Welch's t-test to compare error distributions
between Group 13 ligands and Conventional ligands.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_residuals_with_ligand_labels(
    residuals_path: Path,
    ligand_labels_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load residuals and ligand class labels.
    
    Args:
        residuals_path: Path to residuals.parquet
        ligand_labels_path: Optional path to ligand labels. 
                            If None, expects 'ligand_class' column in residuals.
                            
    Returns:
        Tuple of (residuals_df, ligand_class_series)
    """
    if not residuals_path.exists():
        raise FileNotFoundError(f"Residuals file not found: {residuals_path}")
    
    df = pd.read_parquet(residuals_path)
    
    if ligand_labels_path and ligand_labels_path.exists():
        labels_df = pd.read_json(ligand_labels_path)
        # Merge on a common index or ID column
        # Assuming 'sample_id' or similar exists in both
        common_col = 'sample_id' if 'sample_id' in df.columns and 'sample_id' in labels_df.columns else None
        if common_col:
            df = df.merge(labels_df[['sample_id', 'ligand_class']], on='sample_id', how='inner')
        else:
            # Fallback: assume same order
            df['ligand_class'] = labels_df['ligand_class'].values
    
    if 'ligand_class' not in df.columns:
        raise ValueError("Ligand class information not found in residuals data.")
    
    return df, df['ligand_class']

def perform_welch_ttest(
    residuals_df: pd.DataFrame,
    group_col: str = 'ligand_class',
    error_col: str = 'error',
    group1_name: str = 'Group 13',
    group2_name: str = 'Conventional'
) -> Dict[str, Any]:
    """
    Perform unpaired Welch's t-test between two groups.
    
    Args:
        residuals_df: DataFrame containing errors and group labels
        group_col: Column name for group labels
        error_col: Column name for error values (ML - DFT)
        group1_name: Name of the first group to compare
        group2_name: Name of the second group to compare
        
    Returns:
        Dictionary containing test results
    """
    logger.info(f"Performing Welch's t-test: {group1_name} vs {group2_name}")
    
    # Filter data for each group
    group1_data = residuals_df[residuals_df[group_col] == group1_name][error_col]
    group2_data = residuals_df[residuals_df[group_col] == group2_name][error_col]
    
    n1 = len(group1_data)
    n2 = len(group2_data)
    
    if n1 == 0 or n2 == 0:
        raise ValueError(f"One of the groups has no data. Group1: {n1}, Group2: {n2}")
    
    logger.info(f"Group 13 count: {n1}, Conventional count: {n2}")
    
    # Perform Welch's t-test (unpaired, unequal variance)
    t_stat, p_value = stats.ttest_ind(group1_data, group2_data, equal_var=False)
    
    # Calculate effect size (Cohen's d)
    # Note: Cohen's d is typically for equal variance, but we can compute a version
    # for unequal variance or just report means and stds
    mean1 = group1_data.mean()
    mean2 = group2_data.mean()
    std1 = group1_data.std()
    std2 = group2_data.std()
    
    # Pooled standard deviation for Cohen's d (approximate for unequal variances)
    # Using the formula that accounts for unequal variances
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean1 - mean2) / pooled_std
    
    # 95% Confidence Interval for the difference in means
    # Using Welch-Satterthwaite degrees of freedom
    df_welch = (std1**2 / n1 + std2**2 / n2)**2 / (
        (std1**2 / n1)**2 / (n1 - 1) + (std2**2 / n2)**2 / (n2 - 1)
    )
    
    # Standard error of the difference
    se_diff = np.sqrt(std1**2 / n1 + std2**2 / n2)
    
    # Critical t-value for 95% CI
    t_crit = stats.t.ppf(0.975, df_welch)
    ci_low = (mean1 - mean2) - t_crit * se_diff
    ci_high = (mean1 - mean2) + t_crit * se_diff
    
    result = {
        "test_type": "unpaired_welch_ttest",
        "group1": group1_name,
        "group2": group2_name,
        "group1_count": int(n1),
        "group2_count": int(n2),
        "group1_mean": float(mean1),
        "group2_mean": float(mean2),
        "group1_std": float(std1),
        "group2_std": float(std2),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "degrees_of_freedom": float(df_welch),
        "mean_difference": float(mean1 - mean2),
        "confidence_interval_95": [float(ci_low), float(ci_high)],
        "cohens_d": float(cohens_d),
        "significant_at_005": bool(p_value < 0.05),
        "significant_at_001": bool(p_value < 0.01),
        "interpretation": "Statistically significant difference" if p_value < 0.05 else "No statistically significant difference"
    }
    
    logger.info(f"t-statistic: {t_stat:.4f}, p-value: {p_value:.4e}")
    logger.info(f"Mean difference: {mean1 - mean2:.4f}, 95% CI: [{ci_low:.4f}, {ci_high:.4f}]")
    
    return result

def run_statistical_analysis(
    residuals_path: Path,
    output_path: Path,
    ligand_labels_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run full statistical analysis pipeline.
    
    Args:
        residuals_path: Path to residuals.parquet
        output_path: Path to save results JSON
        ligand_labels_path: Optional path to ligand labels
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Starting statistical analysis for {residuals_path}")
    
    # Load data
    residuals_df, _ = load_residuals_with_ligand_labels(residuals_path, ligand_labels_path)
    
    # Ensure error column exists
    if 'error' not in residuals_df.columns:
        # Try to compute if we have ML and DFT columns
        if 'ml_energy' in residuals_df.columns and 'dft_energy' in residuals_df.columns:
            residuals_df['error'] = residuals_df['ml_energy'] - residuals_df['dft_energy']
            logger.info("Computed error column from ml_energy and dft_energy")
        else:
            raise ValueError("Error column not found and cannot be computed from available columns")
    
    # Run Welch's t-test
    test_results = perform_welch_ttest(
        residuals_df,
        group_col='ligand_class',
        error_col='error',
        group1_name='Group 13',
        group2_name='Conventional'
    )
    
    # Add metadata
    test_results['analysis_timestamp'] = str(pd.Timestamp.now())
    test_results['source_file'] = str(residuals_path)
    test_results['deviation_note'] = (
        "This task implements an UNPAIRED Welch's t-test instead of the paired test "
        "mentioned in FR-006. This deviation is documented in data/results/deviation_log.md "
        "because the ligand classes (Group 13 vs Conventional) represent independent groups "
        "rather than paired samples. Each sample belongs to exactly one ligand class, "
        "making an unpaired test the statistically appropriate choice."
    )
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return test_results

def main():
    """Main entry point for statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical analysis on prediction residuals')
    parser.add_argument('--residuals', type=str, required=True, 
                      help='Path to residuals.parquet')
    parser.add_argument('--output', type=str, default='data/results/statistical_tests.json',
                      help='Path to output JSON file')
    parser.add_argument('--labels', type=str, default=None,
                      help='Optional path to ligand labels JSON')
    
    args = parser.parse_args()
    
    residuals_path = Path(args.residuals)
    output_path = Path(args.output)
    ligand_labels_path = Path(args.labels) if args.labels else None
    
    try:
        results = run_statistical_analysis(
            residuals_path, 
            output_path, 
            ligand_labels_path
        )
        print(f"Analysis complete. Results: {json.dumps(results, indent=2)}")
    except Exception as e:
        logger.error(f"Statistical analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()
