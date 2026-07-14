import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import warnings

from code.analysis.validator import (
    load_prepared_data_ttest,
    load_prepared_data_anova,
    load_prepared_data_chi_squared,
    get_dataset_path
)
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback

def load_prepared_data(dataset_type: str, dataset_name: str) -> Any:
    """
    Loads prepared data for a specific test type from the validator module.
    """
    if dataset_type == 'ttest':
        return load_prepared_data_ttest(dataset_name)
    elif dataset_type == 'anova':
        return load_prepared_data_anova(dataset_name)
    elif dataset_type == 'chi_squared':
        return load_prepared_data_chi_squared(dataset_name)
    else:
        raise ValueError(f"Unknown dataset_type: {dataset_type}")

def run_ttest_on_dataset(dataset_name: str, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Runs an independent t-test on the specified dataset.
    """
    data = load_prepared_data('ttest', dataset_name)
    if data is None:
        return {"error": "Data not found or invalid for t-test"}

    groups = data[group_col].unique()
    if len(groups) != 2:
        return {"error": f"Expected 2 groups for t-test, found {len(groups)}"}

    group1_data = data[data[group_col] == groups[0]][value_col]
    group2_data = data[data[group_col] == groups[1]][value_col]

    if len(group1_data) < 2 or len(group2_data) < 2:
        return {"error": "Insufficient data points for t-test"}

    try:
        t_stat, p_val = stats.ttest_ind(group1_data, group2_data)
        return {
            "test_type": "t-test",
            "dataset": dataset_name,
            "statistic": float(t_stat),
            "p_value": float(p_val),
            "sample_sizes": {str(groups[0]): int(len(group1_data)), str(groups[1]): int(len(group2_data))}
        }
    except Exception as e:
        return {"error": str(e)}

def run_anova_on_dataset(dataset_name: str, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Runs a one-way ANOVA on the specified dataset.
    """
    data = load_prepared_data('anova', dataset_name)
    if data is None:
        return {"error": "Data not found or invalid for ANOVA"}

    groups = data[group_col].unique()
    if len(groups) < 2:
        return {"error": f"Expected at least 2 groups for ANOVA, found {len(groups)}"}

    group_data = [data[data[group_col] == g][value_col] for g in groups]
    group_data = [g.dropna() for g in group_data]

    if any(len(g) < 2 for g in group_data):
        return {"error": "Insufficient data points in one or more groups for ANOVA"}

    try:
        f_stat, p_val = stats.f_oneway(*group_data)
        return {
            "test_type": "anova",
            "dataset": dataset_name,
            "statistic": float(f_stat),
            "p_value": float(p_val),
            "sample_sizes": {str(g): int(len(data[data[group_col] == g])) for g in groups}
        }
    except Exception as e:
        return {"error": str(e)}

def run_chi_squared_on_dataset(dataset_name: str, row_col: str, col_col: str) -> Dict[str, Any]:
    """
    Runs a chi-squared test on the specified dataset.
    """
    data = load_prepared_data('chi_squared', dataset_name)
    if data is None:
        return {"error": "Data not found or invalid for Chi-squared"}

    try:
        contingency_table = pd.crosstab(data[row_col], data[col_col])
        if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
            return {"error": "Contingency table must be at least 2x2"}

        # Use the fallback logic from test_runner/chi_squared_utils
        result = run_chi_squared_with_fallback(contingency_table.values)
        
        return {
            "test_type": "chi-squared",
            "dataset": dataset_name,
            "statistic": float(result['statistic']),
            "p_value": float(result['p_value']),
            "method": result['method'],
            "degrees_of_freedom": int(result.get('dof', 0)),
            "sample_size": int(contingency_table.values.sum())
        }
    except Exception as e:
        return {"error": str(e)}

def save_p_values_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the list of result dictionaries to a CSV file.
    """
    if not results:
        raise ValueError("No results to save.")

    # Flatten nested dictionaries for CSV
    flat_results = []
    for r in results:
        flat_row = {k: v for k, v in r.items() if k != 'error'}
        if 'error' in r:
            flat_row['error'] = r['error']
        # Handle nested sample_sizes dict if present
        if 'sample_sizes' in r and isinstance(r['sample_sizes'], dict):
            for k, v in r['sample_sizes'].items():
                flat_row[f'sample_size_{k}'] = v
            del flat_row['sample_sizes']
        flat_results.append(flat_row)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = list(flat_results[0].keys())
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_results)

def main():
    """
    Main entry point for T031: Run tests on real datasets and save p-values.
    """
    output_path = "data/simulation/real_data_pvalues.csv"
    results = []

    # Define datasets and test configurations
    # Based on T029a/b/c: Breast Cancer (197), Wine (198), Adult (522)
    # We need to map these to the specific test types supported by the validator's prepared data.
    
    configs = [
        # Breast Cancer: Binary classification (Diagnosis), continuous features -> t-test
        # Assuming validator prepared 'Diagnosis' vs 'mean radius' or similar
        {
            "name": "breast_cancer",
            "test": "t-test",
            "group_col": "Diagnosis", # Assuming this column exists after preprocessing
            "value_col": "mean_radius"
        },
        # Wine: Multi-class classification (Class), continuous features -> ANOVA
        {
            "name": "wine",
            "test": "anova",
            "group_col": "Class",
            "value_col": "alcohol"
        },
        # Adult: Two categorical columns for Chi-squared
        # Need to pick two categorical columns. 'Education' and 'Marital-Status' are common.
        {
            "name": "adult",
            "test": "chi-squared",
            "row_col": "Education",
            "col_col": "Marital-Status"
        }
    ]

    print(f"Starting real data validation tests...")

    for config in configs:
        print(f"Running {config['test']} on {config['name']}...")
        try:
            if config['test'] == 't-test':
                res = run_ttest_on_dataset(config['name'], config['group_col'], config['value_col'])
            elif config['test'] == 'anova':
                res = run_anova_on_dataset(config['name'], config['group_col'], config['value_col'])
            elif config['test'] == 'chi-squared':
                res = run_chi_squared_on_dataset(config['name'], config['row_col'], config['col_col'])
            else:
                res = {"error": f"Unknown test type: {config['test']}"}
            
            results.append(res)
            if "error" in res:
                print(f"  Warning: {res['error']}")
            else:
                print(f"  P-value: {res['p_value']:.4f}")
        except Exception as e:
            print(f"  Exception during {config['test']} on {config['name']}: {e}")
            results.append({"test_type": config['test'], "dataset": config['name'], "error": str(e)})

    save_p_values_to_csv(results, output_path)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()