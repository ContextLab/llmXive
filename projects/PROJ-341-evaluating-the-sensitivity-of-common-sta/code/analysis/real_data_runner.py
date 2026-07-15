import os
import csv
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from code.analysis.validator import (
    download_breast_cancer_dataset,
    download_wine_dataset,
    download_adult_dataset,
    prepare_data_for_ttest,
    prepare_data_for_anova,
    prepare_data_for_chi_squared
)

# Paths
REAL_DATA_PVALUES_PATH = "data/simulation/real_data_pvalues.csv"
DATA_RAW_DIR = "data/raw"

def run_ttest_on_dataset(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    group1: str,
    group2: str
) -> Dict[str, Any]:
    """
    Run independent t-test on dataset.
    Returns p-value and test statistics.
    """
    try:
        group1_data = df[df[group_col] == group1][value_col].dropna()
        group2_data = df[df[group_col] == group2][value_col].dropna()
        
        if len(group1_data) < 2 or len(group2_data) < 2:
            return {"p_value": None, "statistic": None, "error": "Insufficient data"}
        
        t_stat, p_val = stats.ttest_ind(group1_data, group2_data)
        
        return {
            "test_type": "t-test",
            "p_value": float(p_val),
            "statistic": float(t_stat),
            "n_group1": len(group1_data),
            "n_group2": len(group2_data)
        }
    except Exception as e:
        return {"test_type": "t-test", "p_value": None, "error": str(e)}

def run_anova_on_dataset(
    df: pd.DataFrame,
    group_col: str,
    value_col: str
) -> Dict[str, Any]:
    """
    Run one-way ANOVA on dataset.
    Returns p-value and F-statistic.
    """
    try:
        groups = df[group_col].unique()
        if len(groups) < 2:
            return {"p_value": None, "statistic": None, "error": "Need at least 2 groups"}
        
        group_data = [df[df[group_col] == g][value_col].dropna() for g in groups]
        
        if any(len(g) < 2 for g in group_data):
            return {"p_value": None, "statistic": None, "error": "Insufficient data in some groups"}
        
        f_stat, p_val = stats.f_oneway(*group_data)
        
        return {
            "test_type": "anova",
            "p_value": float(p_val),
            "statistic": float(f_stat),
            "n_groups": len(groups),
            "groups": list(groups)
        }
    except Exception as e:
        return {"test_type": "anova", "p_value": None, "error": str(e)}

def run_chi_squared_on_dataset(
    df: pd.DataFrame,
    col1: str,
    col2: str
) -> Dict[str, Any]:
    """
    Run chi-squared test of independence on dataset.
    Returns p-value and chi-squared statistic.
    """
    try:
        contingency = pd.crosstab(df[col1], df[col2])
        
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            return {"p_value": None, "statistic": None, "error": "Need 2x2 or larger table"}
        
        chi2_stat, p_val, dof, expected = stats.chi2_contingency(contingency)
        
        return {
            "test_type": "chi-squared",
            "p_value": float(p_val),
            "statistic": float(chi2_stat),
            "degrees_of_freedom": int(dof),
            "table_shape": list(contingency.shape)
        }
    except Exception as e:
        return {"test_type": "chi-squared", "p_value": None, "error": str(e)}

def save_p_values_to_csv(results: List[Dict[str, Any]], output_path: str = REAL_DATA_PVALUES_PATH) -> str:
    """Save p-value results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset', 'test_type', 'p_value', 'statistic', 'details'])
        writer.writeheader()
        
        for result in results:
            row = {
                'dataset': result.get('dataset', 'unknown'),
                'test_type': result.get('test_type', 'unknown'),
                'p_value': result.get('p_value'),
                'statistic': result.get('statistic'),
                'details': json.dumps({k: v for k, v in result.items() if k not in ['dataset', 'test_type', 'p_value', 'statistic']})
            }
            writer.writerow(row)
    
    return output_path

def load_p_values_to_csv_safe(pvalues_path: str = REAL_DATA_PVALUES_PATH) -> List[Dict[str, Any]]:
    """Safely load p-values from CSV."""
    if not os.path.exists(pvalues_path):
        return []
    
    results = []
    with open(pvalues_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def main():
    """Main entry point: download datasets, run tests, save results."""
    print("Running statistical tests on real-world datasets...")
    
    results = []
    
    # 1. Breast Cancer Dataset (T-test)
    try:
        print("Processing Breast Cancer dataset...")
        df_bc = download_breast_cancer_dataset()
        if df_bc is not None:
            # Use diagnosis as group, mean radius as value
            result = run_ttest_on_dataset(df_bc, 'diagnosis', 'radius_mean', 'B', 'M')
            result['dataset'] = 'breast_cancer'
            results.append(result)
    except Exception as e:
        print(f"Error processing Breast Cancer: {e}")
    
    # 2. Wine Dataset (ANOVA)
    try:
        print("Processing Wine dataset...")
        df_wine = download_wine_dataset()
        if df_wine is not None:
            # Use class as group, alcohol as value
            result = run_anova_on_dataset(df_wine, 'class', 'alcohol')
            result['dataset'] = 'wine'
            results.append(result)
    except Exception as e:
        print(f"Error processing Wine: {e}")
    
    # 3. Adult Dataset (Chi-squared)
    try:
        print("Processing Adult dataset...")
        df_adult = download_adult_dataset()
        if df_adult is not None:
            # Use gender and income as categorical variables
            result = run_chi_squared_on_dataset(df_adult, 'gender', 'income')
            result['dataset'] = 'adult'
            results.append(result)
    except Exception as e:
        print(f"Error processing Adult: {e}")
    
    # Save results
    if results:
        output_path = save_p_values_to_csv(results)
        print(f"Results saved to: {output_path}")
        
        # Print summary
        for r in results:
            print(f"{r['dataset']}/{r['test_type']}: p={r.get('p_value')}")
    else:
        print("No results to save.")
    
    return 0

if __name__ == "__main__":
    exit(main())
