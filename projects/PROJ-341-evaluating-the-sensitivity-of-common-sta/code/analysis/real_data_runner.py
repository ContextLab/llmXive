import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Local imports
from code.simulation.logging_config import get_logger
from code.analysis.validator import (
    download_breast_cancer_dataset, 
    download_wine_dataset, 
    download_adult_dataset,
    prepare_data_for_ttest,
    prepare_data_for_anova,
    prepare_data_for_chi_squared,
    load_simulation_metadata,
    save_simulation_metadata,
    compute_file_checksum
)

def load_prepared_data(dataset_name: str) -> Tuple[pd.DataFrame, str]:
    """
    Load prepared data for a specific dataset.
    Assumes T029/T030 have already downloaded and preprocessed the data.
    """
    logger = get_logger()
    data_path = f"data/raw/{dataset_name}_prepared.csv"
    
    if not os.path.exists(data_path):
        logger.warning(f"Prepared data not found for {dataset_name}. Attempting to download and prepare.")
        # If data is missing, we try to run the download/prep logic
        # This acts as a fallback to ensure the pipeline runs
        if dataset_name == 'breast_cancer':
            download_breast_cancer_dataset()
            # Note: The actual prepare logic is in validator.py, 
            # but we assume the main entry point handles the flow.
            # For this specific runner, we expect the file to exist.
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Could not find prepared data for {dataset_name} at {data_path}")
        elif dataset_name == 'wine':
            download_wine_dataset()
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Could not find prepared data for {dataset_name} at {data_path}")
        elif dataset_name == 'adult':
            download_adult_dataset()
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Could not find prepared data for {dataset_name} at {data_path}")
    
    df = pd.read_csv(data_path)
    return df, data_path

def run_ttest_on_dataset(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Run independent t-test on the dataset.
    Assumes the data is prepared with 'group_col' and 'value_col'.
    """
    logger = get_logger()
    try:
        # Split data
        group1 = df[df[group_col] == df[group_col].unique()[0]][value_col]
        group2 = df[df[group_col] == df[group_col].unique()[1]][value_col]
        
        if len(group1) < 2 or len(group2) < 2:
            logger.warning("Insufficient data for t-test")
            return {'p_value': None, 'statistic': None, 'method': 't-test', 'error': 'Insufficient data'}

        # Run t-test
        t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False) # Welch's t-test
        
        result = {
            'p_value': float(p_val),
            'statistic': float(t_stat),
            'method': 't-test',
            'sample_sizes': {'group1': len(group1), 'group2': len(group2)}
        }
        logger.info(f"T-test p-value: {p_val}")
        return result
    except Exception as e:
        logger.error(f"T-test failed: {e}")
        return {'p_value': None, 'statistic': None, 'method': 't-test', 'error': str(e)}

def run_anova_on_dataset(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Run ANOVA on the dataset.
    """
    logger = get_logger()
    try:
        groups = [group[value_col].values for name, group in df.groupby(group_col)]
        
        if len(groups) < 2:
            logger.warning("Insufficient groups for ANOVA")
            return {'p_value': None, 'statistic': None, 'method': 'anova', 'error': 'Insufficient groups'}
        
        f_stat, p_val = stats.f_oneway(*groups)
        
        result = {
            'p_value': float(p_val),
            'statistic': float(f_stat),
            'method': 'anova',
            'num_groups': len(groups)
        }
        logger.info(f"ANOVA p-value: {p_val}")
        return result
    except Exception as e:
        logger.error(f"ANOVA failed: {e}")
        return {'p_value': None, 'statistic': None, 'method': 'anova', 'error': str(e)}

def run_chi_squared_on_dataset(df: pd.DataFrame, col1: str, col2: str) -> Dict[str, Any]:
    """
    Run Chi-squared test on the dataset.
    """
    logger = get_logger()
    try:
        contingency = pd.crosstab(df[col1], df[col2])
        
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            logger.warning("Insufficient categories for Chi-squared")
            return {'p_value': None, 'statistic': None, 'method': 'chi-squared', 'error': 'Insufficient categories'}
        
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
        
        result = {
            'p_value': float(p_val),
            'statistic': float(chi2),
            'method': 'chi-squared',
            'degrees_of_freedom': int(dof),
            'table_shape': contingency.shape
        }
        logger.info(f"Chi-squared p-value: {p_val}")
        return result
    except Exception as e:
        logger.error(f"Chi-squared failed: {e}")
        return {'p_value': None, 'statistic': None, 'method': 'chi-squared', 'error': str(e)}

def save_p_values_to_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Save p-value results to CSV.
    """
    logger = get_logger()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved p-values to {output_path}")
    log_output_file_written(logger, output_path)

def log_output_file_written(logger, path):
    if logger:
        logger.info(f"Output file written: {path}")

def main():
    """
    Main entry point for T031: Run t-test, ANOVA, and chi-squared on real datasets.
    """
    logger = get_logger()
    logger.info("Starting Real Data Runner (T031)")
    
    datasets = [
        ('breast_cancer', 'diagnosis', 'mean_radius'), # Example columns, adjust based on actual prep
        ('wine', 'class', 'alcohol'), # Example
        ('adult', 'class', 'age') # Example
    ]
    
    # We need to know the actual column names after preprocessing.
    # The validator (T030) should have prepared the data.
    # For this implementation, we assume the prepared CSVs have standard columns 
    # or we try to infer them.
    # To be robust, we will try to load the metadata or assume a standard schema.
    
    all_results = []
    
    for dataset_name, group_col_guess, value_col_guess in datasets:
        try:
            logger.info(f"Processing dataset: {dataset_name}")
            df, path = load_prepared_data(dataset_name)
            
            # Attempt to run tests. 
            # Since column names might vary, we try to find suitable columns dynamically
            # or use the ones passed if they exist.
            
            # Fallback: If specific columns not found, try to find numeric and categorical
            if group_col_guess not in df.columns:
                # Try to find a categorical column
                cat_cols = df.select_dtypes(include=['object', 'category']).columns
                if len(cat_cols) > 0:
                    group_col_guess = cat_cols[0]
            
            if value_col_guess not in df.columns:
                num_cols = df.select_dtypes(include=['number']).columns
                if len(num_cols) > 0:
                    value_col_guess = num_cols[0]
            
            if group_col_guess not in df.columns or value_col_guess not in df.columns:
                logger.warning(f"Could not find suitable columns for {dataset_name}. Skipping.")
                continue

            # Run T-Test
            ttest_res = run_ttest_on_dataset(df, group_col_guess, value_col_guess)
            ttest_res['dataset'] = dataset_name
            ttest_res['test_type'] = 't-test'
            all_results.append(ttest_res)
            
            # Run ANOVA (requires >2 groups ideally, but can run with 2)
            anova_res = run_anova_on_dataset(df, group_col_guess, value_col_guess)
            anova_res['dataset'] = dataset_name
            anova_res['test_type'] = 'anova'
            all_results.append(anova_res)
            
            # Run Chi-Squared (requires two categorical columns)
            # Find two categorical columns
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) >= 2:
                chi_res = run_chi_squared_on_dataset(df, cat_cols[0], cat_cols[1])
                chi_res['dataset'] = dataset_name
                chi_res['test_type'] = 'chi-squared'
                all_results.append(chi_res)
            else:
                logger.warning(f"Not enough categorical columns for Chi-squared in {dataset_name}")
                all_results.append({
                    'dataset': dataset_name,
                    'test_type': 'chi-squared',
                    'p_value': None,
                    'statistic': None,
                    'method': 'chi-squared',
                    'error': 'Insufficient categorical columns'
                })

        except Exception as e:
            logger.error(f"Error processing {dataset_name}: {e}")
            all_results.append({
                'dataset': dataset_name,
                'test_type': 'error',
                'p_value': None,
                'statistic': None,
                'method': 'error',
                'error': str(e)
            })
    
    output_path = "data/simulation/real_data_pvalues.csv"
    save_p_values_to_csv(all_results, output_path)
    
    logger.info("Real Data Runner completed.")

if __name__ == "__main__":
    main()
