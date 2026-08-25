"""
Comparative analysis logic for User Story 3.

Calculates the difference in Type I and Type II error rates between baseline
and each augmentation method.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Import existing utilities from the project API
from analyze import load_simulation_results, calculate_error_rates, calculate_bootstrap_ci

logger = logging.getLogger(__name__)

def load_all_results(results_dir: Path) -> Dict[str, Any]:
    """
    Load all result JSON files from the results directory.
    
    Args:
        results_dir: Path to the results directory.
        
    Returns:
        Dictionary mapping file paths to their loaded JSON content.
    """
    results = {}
    if not results_dir.exists():
        logger.warning(f"Results directory {results_dir} does not exist.")
        return results
    
    for json_file in results_dir.glob("**/*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                results[str(json_file)] = data
                logger.debug(f"Loaded results from {json_file}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {json_file}: {e}")
    
    return results

def categorize_results(results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Categorize results by dataset, sample size, condition (null/alt), and method.
    
    Args:
        results: Dictionary of loaded result JSONs.
        
    Returns:
        Nested dictionary: {dataset: {size: {condition: {method: data}}}}
    """
    categorized = {}
    
    for filepath, data in results.items():
        # Extract metadata from filename or data structure
        # Expected filename pattern: [dataset]_[size]_[method]_[condition].json
        # or [dataset]_[size]_baseline_[condition].json
        filename = os.path.basename(filepath)
        parts = filename.replace('.json', '').split('_')
        
        if len(parts) < 4:
            logger.warning(f"Skipping file with unexpected name format: {filename}")
            continue
        
        # Heuristic to parse filename parts
        # Last part is condition (null/alt)
        condition = parts[-1]
        # Second to last might be method or 'baseline'
        # If baseline, then third to last is size
        if parts[-2] == 'baseline':
            method = 'baseline'
            size = parts[-3]
            dataset = '_'.join(parts[:-3])
        else:
            method = parts[-2]
            size = parts[-3]
            dataset = '_'.join(parts[:-3])
        
        # Validate condition
        if condition not in ['null', 'alt']:
            logger.warning(f"Invalid condition '{condition}' in {filename}, skipping.")
            continue
        
        if dataset not in categorized:
            categorized[dataset] = {}
        if size not in categorized[dataset]:
            categorized[dataset][size] = {'null': {}, 'alt': {}}
        
        categorized[dataset][size][condition][method] = data
    
    return categorized

def calculate_error_rate_difference(
    baseline_data: Dict[str, Any], 
    augmented_data: Dict[str, Any],
    condition: str,
    metric: str = 'type_i_error_rate'
) -> Dict[str, Any]:
    """
    Calculate the difference in error rates between baseline and augmented data.
    
    Args:
        baseline_data: Baseline result dictionary.
        augmented_data: Augmented result dictionary.
        condition: 'null' or 'alt'.
        metric: The error rate metric to compare ('type_i_error_rate' or 'type_ii_error_rate').
                
    Returns:
        Dictionary containing baseline rate, augmented rate, difference, and confidence info.
    """
    # Extract error rates
    baseline_rate = baseline_data.get('error_rates', {}).get(metric, None)
    augmented_rate = augmented_data.get('error_rates', {}).get(metric, None)
    
    if baseline_rate is None or augmented_rate is None:
        logger.warning(f"Missing {metric} in one of the datasets. Skipping comparison.")
        return {
            'baseline_rate': None,
            'augmented_rate': None,
            'difference': None,
            'status': 'missing_data'
        }
    
    difference = augmented_rate - baseline_rate
    
    # Calculate bootstrap CI for the difference if we have raw p-values
    # This is a simplified approach; ideally we'd resample the difference directly
    # For now, we rely on the summary stats provided
    diff_ci_lower = None
    diff_ci_upper = None
    
    # Attempt to compute CI for difference using delta method approximation
    # or simply report the point estimate if raw data isn't available in the summary
    # The analyze.py module has calculate_bootstrap_ci, but it expects p-values.
    # Here we assume the summary JSON has the rates and we report the point difference.
    
    return {
        'baseline_rate': baseline_rate,
        'augmented_rate': augmented_rate,
        'difference': difference,
        'ci_lower': diff_ci_lower,
        'ci_upper': diff_ci_upper,
        'status': 'calculated'
    }

def generate_comparative_analysis(
    categorized_results: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]]
) -> pd.DataFrame:
    """
    Generate a comprehensive comparative analysis DataFrame.
    
    Args:
        categorized_results: Nested dictionary of results.
        
    Returns:
        DataFrame with columns: dataset, size, condition, method, metric, baseline_rate, augmented_rate, difference
    """
    rows = []
    
    methods = ['gaussian', 'smote', 'random_oversampling']
    metrics = ['type_i_error_rate', 'type_ii_error_rate']
    conditions = ['null', 'alt']
    
    for dataset, sizes in categorized_results.items():
        for size, conditions_data in sizes.items():
            for condition, methods_data in conditions_data.items():
                if 'baseline' not in methods_data:
                    logger.warning(f"No baseline found for {dataset}_{size}_{condition}, skipping.")
                    continue
                
                baseline_data = methods_data['baseline']
                
                for method in methods:
                    if method not in methods_data:
                        continue
                    
                    augmented_data = methods_data[method]
                    
                    for metric in metrics:
                        comparison = calculate_error_rate_difference(
                            baseline_data, augmented_data, condition, metric
                        )
                        
                        if comparison['status'] == 'calculated':
                            rows.append({
                                'dataset': dataset,
                                'size': int(size),
                                'condition': condition,
                                'method': method,
                                'metric': metric,
                                'baseline_rate': comparison['baseline_rate'],
                                'augmented_rate': comparison['augmented_rate'],
                                'difference': comparison['difference'],
                                'ci_lower': comparison['ci_lower'],
                                'ci_upper': comparison['ci_upper']
                            })
    
    return pd.DataFrame(rows)

def save_comparative_analysis(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the comparative analysis to a CSV file.
    
    Args:
        df: The comparative analysis DataFrame.
        output_path: Path to save the CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved comparative analysis to {output_path}")

def main():
    """Main entry point for comparative analysis."""
    logging.basicConfig(level=logging.INFO)
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    results_dir = project_root / 'results'
    output_file = project_root / 'data' / 'derived' / 'comparative_analysis.csv'
    
    logger.info(f"Loading results from {results_dir}")
    results = load_all_results(results_dir)
    
    if not results:
        logger.error("No results found. Exiting.")
        return
    
    logger.info(f"Loaded {len(results)} result files.")
    
    logger.info("Categorizing results...")
    categorized = categorize_results(results)
    
    logger.info("Generating comparative analysis...")
    df = generate_comparative_analysis(categorized)
    
    if df.empty:
        logger.warning("No comparative data could be generated. Check result files.")
        return
    
    logger.info(f"Analysis complete. Rows: {len(df)}")
    save_comparative_analysis(df, output_file)
    
    # Print summary
    print("\n--- Comparative Analysis Summary ---")
    print(df.groupby(['dataset', 'size', 'condition', 'metric'])['difference'].describe())
    print("------------------------------------")

if __name__ == '__main__':
    main()
