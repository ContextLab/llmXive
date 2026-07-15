import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation.logging_config import get_logger
from code.analysis.validator import (
    download_breast_cancer_dataset, download_wine_dataset, download_adult_dataset,
    prepare_data_for_ttest, prepare_data_for_anova, prepare_data_for_chi_squared
)

logger = get_logger(__name__)

def run_ttest_on_dataset(features: pd.DataFrame, targets: pd.DataFrame, 
                         target_column: Optional[str] = None, 
                         feature_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Run t-test on dataset.
    
    Args:
        features: DataFrame with features
        targets: DataFrame with targets
        target_column: Name of target column
        feature_column: Name of feature column
        
    Returns:
        Dictionary with test results
    """
    try:
        group1, group2 = prepare_data_for_ttest(features, targets, target_column, feature_column)
        
        if len(group1) < 2 or len(group2) < 2:
            logger.warning("Insufficient data for t-test")
            return {'test_type': 't-test', 'p_value': np.nan, 'statistic': np.nan, 'error': 'Insufficient data'}
        
        statistic, p_value = stats.ttest_ind(group1, group2)
        
        return {
            'test_type': 't-test',
            'p_value': p_value,
            'statistic': statistic,
            'n_group1': len(group1),
            'n_group2': len(group2)
        }
    except Exception as e:
        logger.error(f"Error running t-test: {str(e)}")
        return {'test_type': 't-test', 'p_value': np.nan, 'statistic': np.nan, 'error': str(e)}

def run_anova_on_dataset(features: pd.DataFrame, targets: pd.DataFrame, 
                         target_column: Optional[str] = None, 
                         feature_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Run ANOVA test on dataset.
    
    Args:
        features: DataFrame with features
        targets: DataFrame with targets
        target_column: Name of target column
        feature_column: Name of feature column
        
    Returns:
        Dictionary with test results
    """
    try:
        groups = prepare_data_for_anova(features, targets, target_column, feature_column)
        
        if len(groups) < 2:
            logger.warning("Insufficient groups for ANOVA")
            return {'test_type': 'anova', 'p_value': np.nan, 'statistic': np.nan, 'error': 'Insufficient groups'}
        
        # Check for empty groups
        groups = [g for g in groups if len(g) > 0]
        if len(groups) < 2:
            logger.warning("Not enough non-empty groups for ANOVA")
            return {'test_type': 'anova', 'p_value': np.nan, 'statistic': np.nan, 'error': 'Not enough groups'}
        
        statistic, p_value = stats.f_oneway(*groups)
        
        return {
            'test_type': 'anova',
            'p_value': p_value,
            'statistic': statistic,
            'n_groups': len(groups),
            'n_per_group': [len(g) for g in groups]
        }
    except Exception as e:
        logger.error(f"Error running ANOVA: {str(e)}")
        return {'test_type': 'anova', 'p_value': np.nan, 'statistic': np.nan, 'error': str(e)}

def run_chi_squared_on_dataset(features: pd.DataFrame, targets: pd.DataFrame, 
                               feature_column: Optional[str] = None, 
                               target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Run chi-squared test on dataset.
    
    Args:
        features: DataFrame with features
        targets: DataFrame with targets
        feature_column: Name of feature column
        target_column: Name of target column
        
    Returns:
        Dictionary with test results
    """
    try:
        contingency = prepare_data_for_chi_squared(features, targets, feature_column, target_column)
        
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            logger.warning("Contingency table too small for chi-squared")
            return {'test_type': 'chi-squared', 'p_value': np.nan, 'statistic': np.nan, 'error': 'Table too small'}
        
        # Use fallback logic for low expected counts
        result = run_chi_squared_with_fallback(contingency)
        
        return {
            'test_type': 'chi-squared',
            'p_value': result['p_value'],
            'statistic': result['statistic'],
            'method': result['method'],
            'shape': list(contingency.shape)
        }
    except Exception as e:
        logger.error(f"Error running chi-squared: {str(e)}")
        return {'test_type': 'chi-squared', 'p_value': np.nan, 'statistic': np.nan, 'error': str(e)}

def save_p_values_to_csv(results: List[Dict[str, Any]], filepath: str = 'data/simulation/real_data_pvalues.csv'):
    """
    Save p-values to CSV file.
    
    Args:
        results: List of result dictionaries
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} p-values to {filepath}")

def load_p_values_to_csv_safe(filepath: str = 'data/simulation/real_data_pvalues.csv') -> pd.DataFrame:
    """
    Load p-values from CSV file safely.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        DataFrame with p-values
    """
    if not os.path.exists(filepath):
        logger.warning(f"P-values file not found: {filepath}")
        return pd.DataFrame()
    
    return pd.read_csv(filepath)

def run_validation_on_datasets(datasets: List[str] = None) -> List[Dict[str, Any]]:
    """
    Run validation tests on all specified datasets.
    
    Args:
        datasets: List of dataset names (default: all)
        
    Returns:
        List of result dictionaries
    """
    if datasets is None:
        datasets = ['breast_cancer', 'wine', 'adult']
    
    all_results = []
    
    for dataset_name in datasets:
        logger.info(f"Running validation on {dataset_name} dataset...")
        
        try:
            if dataset_name == 'breast_cancer':
                features, targets = download_breast_cancer_dataset()
            elif dataset_name == 'wine':
                features, targets = download_wine_dataset()
            elif dataset_name == 'adult':
                features, targets = download_adult_dataset()
            else:
                logger.warning(f"Unknown dataset: {dataset_name}")
                continue
            
            # Run t-test
            ttest_result = run_ttest_on_dataset(features, targets)
            ttest_result['dataset'] = dataset_name
            all_results.append(ttest_result)
            
            # Run ANOVA (only if more than 2 classes)
            if len(targets[targets.columns[0]].unique()) > 2:
                anova_result = run_anova_on_dataset(features, targets)
                anova_result['dataset'] = dataset_name
                all_results.append(anova_result)
            
            # Run chi-squared
            chi_result = run_chi_squared_on_dataset(features, targets)
            chi_result['dataset'] = dataset_name
            all_results.append(chi_result)
            
        except Exception as e:
            logger.error(f"Error processing {dataset_name}: {str(e)}")
            all_results.append({
                'dataset': dataset_name,
                'test_type': 'error',
                'p_value': np.nan,
                'statistic': np.nan,
                'error': str(e)
            })
    
    return all_results

def main():
    """Main function to run validation on all datasets."""
    try:
        logger.info("Starting real data validation...")
        
        results = run_validation_on_datasets()
        
        save_p_values_to_csv(results)
        
        logger.info(f"Completed validation. {len(results)} tests run.")
        
        # Print summary
        for result in results:
            if 'p_value' in result and not np.isnan(result['p_value']):
                logger.info(f"{result['dataset']} - {result['test_type']}: p={result['p_value']:.4f}")
            else:
                logger.warning(f"{result['dataset']} - {result['test_type']}: FAILED - {result.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in real data validation: {str(e)}")
        raise

if __name__ == '__main__':
    main()
