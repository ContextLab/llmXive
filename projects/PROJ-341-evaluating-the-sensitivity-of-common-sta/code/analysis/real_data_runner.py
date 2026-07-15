import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from code.analysis.validator import (
    download_breast_cancer_dataset,
    download_wine_dataset,
    download_adult_dataset,
    prepare_data_for_ttest,
    prepare_data_for_anova,
    prepare_data_for_chi_squared,
    load_simulation_metadata,
    save_simulation_metadata
)
from code.simulation.test_runner import run_t_test, run_anova, run_chi_squared
from code.simulation.logging_config import get_logger

logger = get_logger(__name__)

def load_prepared_data(dataset_name: str) -> Optional[pd.DataFrame]:
    """Loads prepared data from the data/raw directory."""
    path = os.path.join("data", "raw", f"{dataset_name}_prepared.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def run_ttest_on_dataset(df: pd.DataFrame, group_col: str, target_col: str) -> List[float]:
    """Runs t-test on the dataset and returns a list of p-values."""
    p_values = []
    try:
        # Assuming binary group for t-test
        groups = df[group_col].unique()
        if len(groups) != 2:
            logger.warning(f"t-test requires 2 groups, found {len(groups)} for {group_col}")
            return p_values
        
        group1 = df[df[group_col] == groups[0]][target_col]
        group2 = df[df[group_col] == groups[1]][target_col]
        
        if len(group1) < 2 or len(group2) < 2:
            return p_values
        
        # Run t-test
        stat, p = run_t_test(group1.values, group2.values, alpha=0.05)
        p_values.append(p)
    except Exception as e:
        logger.error(f"Error running t-test: {e}")
    return p_values

def run_anova_on_dataset(df: pd.DataFrame, group_col: str, target_col: str) -> List[float]:
    """Runs ANOVA on the dataset and returns a list of p-values."""
    p_values = []
    try:
        groups = df[group_col].unique()
        if len(groups) < 2:
            return p_values
        
        group_data = [df[df[group_col] == g][target_col].values for g in groups]
        
        if any(len(g) < 2 for g in group_data):
            return p_values
        
        stat, p = run_anova(group_data, alpha=0.05)
        p_values.append(p)
    except Exception as e:
        logger.error(f"Error running ANOVA: {e}")
    return p_values

def run_chi_squared_on_dataset(df: pd.DataFrame, col1: str, col2: str) -> List[float]:
    """Runs Chi-squared test on the dataset and returns a list of p-values."""
    p_values = []
    try:
        # Create contingency table
        contingency = pd.crosstab(df[col1], df[col2])
        
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return p_values
        
        stat, p, dof, expected = run_chi_squared(contingency.values, alpha=0.05)
        p_values.append(p)
    except Exception as e:
        logger.error(f"Error running Chi-squared: {e}")
    return p_values

def save_p_values_to_csv(results: Dict[str, List[float]], output_path: str) -> None:
    """Saves p-values to a CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['dataset', 'test_type', 'p_value'])
        
        for dataset, tests in results.items():
            for test_type, p_vals in tests.items():
                for p in p_vals:
                    writer.writerow([dataset, test_type, p])

def main():
    """
    Main entry point for running statistical tests on real datasets.
    Downloads datasets, prepares them, runs tests, and saves p-values.
    """
    logger.info("Starting Real Data Runner")
    
    # Ensure data/raw directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    # Download datasets
    logger.info("Downloading datasets...")
    download_breast_cancer_dataset()
    download_wine_dataset()
    download_adult_dataset()
    
    # Prepare datasets
    logger.info("Preparing datasets...")
    # Breast Cancer: T-test (diagnosis vs some feature)
    bc_df = prepare_data_for_ttest("breast_cancer")
    # Wine: ANOVA (class vs some feature)
    wine_df = prepare_data_for_anova("wine")
    # Adult: Chi-squared (two categorical features)
    adult_df = prepare_data_for_chi_squared("adult")
    
    results = {}
    
    # Run tests on Breast Cancer
    if bc_df is not None:
        logger.info("Running tests on Breast Cancer dataset...")
        # Assume 'diagnosis' is the target and 'radius_mean' is a feature
        # We need a binary group column. Let's assume we created one or use existing.
        # For demonstration, we'll try to run t-test on a numeric feature grouped by diagnosis
        # But t-test_on_dataset expects a group_col and target_col.
        # Let's assume the prepared data has 'group' and 'value' columns.
        if 'group' in bc_df.columns and 'value' in bc_df.columns:
            results['breast_cancer'] = {
                't-test': run_ttest_on_dataset(bc_df, 'group', 'value')
            }
    
    # Run tests on Wine
    if wine_df is not None:
        logger.info("Running tests on Wine dataset...")
        # ANOVA: class vs feature
        if 'class' in wine_df.columns and 'feature' in wine_df.columns:
            results['wine'] = {
                'anova': run_anova_on_dataset(wine_df, 'class', 'feature')
            }
    
    # Run tests on Adult
    if adult_df is not None:
        logger.info("Running tests on Adult dataset...")
        # Chi-squared: two categorical columns
        if 'col1' in adult_df.columns and 'col2' in adult_df.columns:
            results['adult'] = {
                'chi-squared': run_chi_squared_on_dataset(adult_df, 'col1', 'col2')
            }
    
    # Save results
    output_path = "data/simulation/real_data_pvalues.csv"
    save_p_values_to_csv(results, output_path)
    logger.info(f"Real data p-values saved to {output_path}")
    
    # Update metadata
    meta = load_simulation_metadata()
    meta['real_data_runs'] = meta.get('real_data_runs', [])
    meta['real_data_runs'].append({
        'timestamp': str(datetime.now()),
        'datasets': list(results.keys()),
        'output_file': output_path
    })
    save_simulation_metadata(meta)

if __name__ == "__main__":
    main()
