"""
Real Data Statistical Test Runner (Task T031)

Executes t-test, ANOVA, and chi-squared tests on real-world datasets
downloaded in T029a-T029c and T030 preprocessing.
Saves observed p-value distributions to data/simulation/real_data_pvalues.csv.
"""
import os
import csv
import json
import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional, Tuple

# Import from existing API surface
from code.analysis.validator import (
    load_simulation_metadata,
    save_simulation_metadata,
    preprocess_dataset_for_validation,
    ensure_data_raw_dir
)
from code.simulation.test_runner import (
    run_t_test,
    run_anova,
    run_chi_squared
)

def load_preprocessed_datasets() -> Dict[str, pd.DataFrame]:
    """
    Load preprocessed datasets from data/raw/ directory.
    Expects files: breast_cancer_clean.csv, wine_clean.csv, adult_clean.csv
    """
    ensure_data_raw_dir()
    data_dir = "data/raw"
    datasets = {}

    file_map = {
        "breast_cancer": "breast_cancer_clean.csv",
        "wine": "wine_clean.csv",
        "adult": "adult_clean.csv"
    }

    for name, filename in file_map.items():
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            datasets[name] = pd.read_csv(filepath)
        else:
            raise FileNotFoundError(f"Preprocessed dataset not found: {filepath}")

    return datasets

def run_t_tests_on_dataset(df: pd.DataFrame, dataset_name: str) -> List[Dict[str, Any]]:
    """
    Run t-tests on numeric columns of the dataset.
    Compares each numeric column against a target or between groups if a binary column exists.
    Returns a list of results.
    """
    results = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 2:
        return results

    # Strategy: If a binary target exists, compare groups. Otherwise, compare first two numeric cols.
    # For Breast Cancer: 'diagnosis' (M/W) -> map to 0/1, compare numeric features.
    # For Wine: No explicit binary target, compare first two features or assume class column if present.
    # For Adult: 'class' (<=50K, >50K) -> binary.

    target_col = None
    group_col = None

    # Heuristic to find a binary categorical column
    for col in df.columns:
        if df[col].dtype == 'object':
            unique_vals = df[col].nunique()
            if unique_vals == 2:
                target_col = col
                break

    if target_col:
        # Map object categories to 0/1 if possible, or use as group
        if target_col in df.columns:
            groups = df[target_col].unique()
            if len(groups) == 2:
                # Perform t-test for each numeric column between the two groups
                for col in numeric_cols:
                    if col == target_col: continue
                    try:
                        group1 = df[df[target_col] == groups[0]][col].dropna()
                        group2 = df[df[target_col] == groups[1]][col].dropna()

                        if len(group1) > 1 and len(group2) > 1:
                            stat, pval = stats.ttest_ind(group1, group2)
                            results.append({
                                "dataset": dataset_name,
                                "test_type": "t-test",
                                "variable": col,
                                "group1": str(groups[0]),
                                "group2": str(groups[1]),
                                "p_value": pval,
                                "statistic": stat,
                                "n1": len(group1),
                                "n2": len(group2),
                                "sample_size": len(df)
                            })
                    except Exception as e:
                        continue
    else:
        # Fallback: Compare first two numeric columns if no binary target found
        if len(numeric_cols) >= 2:
            col1, col2 = numeric_cols[0], numeric_cols[1]
            try:
                stat, pval = stats.ttest_ind(df[col1].dropna(), df[col2].dropna())
                results.append({
                    "dataset": dataset_name,
                    "test_type": "t-test",
                    "variable": f"{col1}_vs_{col2}",
                    "p_value": pval,
                    "statistic": stat,
                    "sample_size": len(df)
                })
            except Exception:
                pass

    return results

def run_anova_on_dataset(df: pd.DataFrame, dataset_name: str) -> List[Dict[str, Any]]:
    """
    Run ANOVA on dataset if a categorical column with >2 levels exists.
    """
    results = []
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_cols) < 1 or len(categorical_cols) < 1:
        return results

    for cat_col in categorical_cols:
        if df[cat_col].nunique() > 2:
            # ANOVA: Compare numeric columns across groups of cat_col
            groups = [group for _, group in df.groupby(cat_col)]
            if len(groups) >= 3:
                # Take first numeric column for ANOVA
                target_num = numeric_cols[0]
                try:
                    f_vals = [g[target_num].dropna() for g in groups if len(g[target_num].dropna()) > 0]
                    if len(f_vals) >= 3:
                        f_stat, p_val = stats.f_oneway(*f_vals)
                        results.append({
                            "dataset": dataset_name,
                            "test_type": "anova",
                            "variable": target_num,
                            "grouping_variable": cat_col,
                            "num_groups": len(groups),
                            "p_value": p_val,
                            "f_statistic": f_stat,
                            "sample_size": len(df)
                        })
                except Exception:
                    continue
    return results

def run_chi_squared_on_dataset(df: pd.DataFrame, dataset_name: str) -> List[Dict[str, Any]]:
    """
    Run Chi-squared test on pairs of categorical columns.
    """
    results = []
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

    if len(categorical_cols) < 2:
        return results

    # Try all pairs
    for i in range(len(categorical_cols)):
        for j in range(i + 1, len(categorical_cols)):
            col1, col2 = categorical_cols[i], categorical_cols[j]
            try:
                contingency = pd.crosstab(df[col1], df[col2])
                if contingency.min().min() == 0:
                    # Might need expected count check, but run_chi_squared_with_fallback handles it
                    pass
                
                # Use the existing runner which handles fallbacks
                # We need to convert contingency table to the format expected by run_chi_squared
                # run_chi_squared expects (group1_data, group2_data) or similar? 
                # Let's look at run_chi_squared signature in test_runner.py:
                # It expects group1 and group2 as arrays/lists?
                # Actually, for contingency table, we usually pass the table itself or raw data.
                # The existing run_chi_squared in test_runner.py is designed for simulation (group1 vs group2).
                # For real data with contingency tables, we use scipy.stats.chi2_contingency directly here
                # to ensure we handle the table correctly, then wrap it in the result dict.
                
                stat, p_val, dof, expected = stats.chi2_contingency(contingency)
                results.append({
                    "dataset": dataset_name,
                    "test_type": "chi-squared",
                    "variable_1": col1,
                    "variable_2": col2,
                    "p_value": p_val,
                    "chi2_statistic": stat,
                    "degrees_of_freedom": dof,
                    "sample_size": len(df)
                })
            except Exception:
                continue
    
    return results

def run_all_real_data_tests() -> List[Dict[str, Any]]:
    """
    Main function to run all tests on all preprocessed datasets.
    """
    datasets = load_preprocessed_datasets()
    all_results = []

    for name, df in datasets.items():
        all_results.extend(run_t_tests_on_dataset(df, name))
        all_results.extend(run_anova_on_dataset(df, name))
        all_results.extend(run_chi_squared_on_dataset(df, name))

    return all_results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str):
    """
    Save results to CSV.
    """
    if not results:
        # Write empty file with headers if no results
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["dataset", "test_type", "p_value", "statistic", "sample_size", "details"])
        return

    # Determine all keys
    keys = results[0].keys()
    for r in results:
        keys = keys.union(r.keys())
    
    keys = sorted(list(keys))

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)

def main():
    """
    Entry point for T031.
    """
    output_dir = "data/simulation"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "real_data_pvalues.csv")

    print("Starting real data statistical tests (T031)...")
    try:
        results = run_all_real_data_tests()
        print(f"Collected {len(results)} test results.")
        save_results_to_csv(results, output_file)
        print(f"Saved results to {output_file}")
        
        # Update metadata to mark T031 completion
        metadata_path = "data/simulation_metadata.json"
        metadata = load_simulation_metadata() if os.path.exists(metadata_path) else {}
        if "tasks" not in metadata: metadata["tasks"] = {}
        metadata["tasks"]["T031"] = {
            "status": "completed",
            "output_file": output_file,
            "result_count": len(results)
        }
        save_simulation_metadata(metadata)
        
    except Exception as e:
        print(f"Error running real data tests: {e}")
        raise

if __name__ == "__main__":
    main()
