"""
Generate statistical report from paired Wilcoxon tests.

This script reads per_sample_errors.csv, runs paired Wilcoxon tests
for all method pairs within each dataset, and outputs results to
results/statistical_report.csv.

Output columns: dataset, method_pair, test_type, p_value, significance_flag
"""
import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from stats.significance import run_paired_wilcoxon
from utils.logger import get_logger

logger = get_logger(__name__)

def load_per_sample_errors(filepath: Path) -> pd.DataFrame:
    """Load and validate per-sample errors file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Per-sample errors file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    required_cols = ['sample_id', 'method', 'prediction', 'lower_bound', 
                    'upper_bound', 'ground_truth', 'dataset']
    
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    logger.info(f"Loaded {len(df)} per-sample error records from {filepath}")
    return df

def generate_method_pairs(methods: List[str]) -> List[Tuple[str, str]]:
    """Generate all unique pairs of methods for comparison."""
    pairs = []
    for i in range(len(methods)):
        for j in range(i + 1, len(methods)):
            pairs.append((methods[i], methods[j]))
    return pairs

def run_statistical_tests(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run paired Wilcoxon tests for all method pairs within each dataset.
    
    Returns DataFrame with columns: dataset, method_pair, test_type, p_value, significance_flag
    """
    results = []
    
    # Group by dataset
    datasets = df['dataset'].unique()
    
    for dataset in datasets:
        dataset_df = df[df['dataset'] == dataset]
        methods = dataset_df['method'].unique().tolist()
        
        if len(methods) < 2:
            logger.warning(f"Dataset {dataset} has fewer than 2 methods ({methods}), skipping")
            continue
        
        # Generate all method pairs
        method_pairs = generate_method_pairs(methods)
        
        for method1, method2 in method_pairs:
            try:
                # Extract errors for both methods
                mask1 = (dataset_df['method'] == method1)
                mask2 = (dataset_df['method'] == method2)
                
                errors1 = dataset_df[mask1]['prediction'] - dataset_df[mask1]['ground_truth']
                errors2 = dataset_df[mask2]['prediction'] - dataset_df[mask2]['ground_truth']
                
                # Ensure same sample_id alignment (paired test)
                sample_ids1 = set(dataset_df[mask1]['sample_id'])
                sample_ids2 = set(dataset_df[mask2]['sample_id'])
                
                common_samples = sample_ids1.intersection(sample_ids2)
                if len(common_samples) < 10:
                    logger.warning(
                        f"Dataset {dataset}, pair ({method1}, {method2}): "
                        f"Only {len(common_samples)} common samples, marking inconclusive"
                    )
                    results.append({
                        'dataset': dataset,
                        'method_pair': f"{method1} vs {method2}",
                        'test_type': 'paired_wilcoxon',
                        'p_value': None,
                        'significance_flag': 'inconclusive'
                    })
                    continue
                
                # Filter to common samples and align
                common_list = sorted(list(common_samples))
                errors1_aligned = dataset_df[mask1][dataset_df[mask1]['sample_id'].isin(common_list)]
                errors2_aligned = dataset_df[mask2][dataset_df[mask2]['sample_id'].isin(common_list)]
                
                # Sort by sample_id to ensure alignment
                errors1_aligned = errors1_aligned.sort_values('sample_id')['prediction'] - errors1_aligned.sort_values('sample_id')['ground_truth']
                errors2_aligned = errors2_aligned.sort_values('sample_id')['prediction'] - errors2_aligned.sort_values('sample_id')['ground_truth']
                
                # Run paired Wilcoxon test
                stat, p_value = run_paired_wilcoxon(
                    errors1_aligned.values, 
                    errors2_aligned.values
                )
                
                # Determine significance (alpha = 0.05)
                significance = 'significant' if p_value < 0.05 else 'not_significant'
                
                results.append({
                    'dataset': dataset,
                    'method_pair': f"{method1} vs {method2}",
                    'test_type': 'paired_wilcoxon',
                    'p_value': p_value,
                    'significance_flag': significance
                })
                
                logger.info(
                    f"Dataset {dataset}, pair ({method1}, {method2}): "
                    f"p-value = {p_value:.4f}, {significance}"
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to run test for dataset {dataset}, pair ({method1}, {method2}): {e}"
                )
                results.append({
                    'dataset': dataset,
                    'method_pair': f"{method1} vs {method2}",
                    'test_type': 'paired_wilcoxon',
                    'p_value': None,
                    'significance_flag': 'error'
                })
    
    return pd.DataFrame(results)

def main():
    """Main entry point for generating statistical report."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "results" / "per_sample_errors.csv"
    output_path = base_dir / "results" / "statistical_report.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting statistical report generation")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    try:
        # Load per-sample errors
        df = load_per_sample_errors(input_path)
        
        # Run statistical tests
        report_df = run_statistical_tests(df)
        
        # Save report
        report_df.to_csv(output_path, index=False)
        
        logger.info(f"Statistical report saved to {output_path}")
        logger.info(f"Generated {len(report_df)} test results")
        
        # Print summary
        print("\n=== Statistical Report Summary ===")
        print(f"Total tests: {len(report_df)}")
        print(f"Significant: {len(report_df[report_df['significance_flag'] == 'significant'])}")
        print(f"Not significant: {len(report_df[report_df['significance_flag'] == 'not_significant'])}")
        print(f"Inconclusive/Errors: {len(report_df[report_df['significance_flag'].isin(['inconclusive', 'error'])])}")
        print(f"\nReport saved to: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file not found: {e}")
        print(f"ERROR: {e}")
        print("Please ensure per_sample_errors.csv has been generated by running the pipeline first.")
        raise
    except Exception as e:
        logger.error(f"Failed to generate statistical report: {e}")
        print(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
