import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from ucimlrepo import fetch_ucirepo
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback

def ensure_data_raw_dir():
    """Ensure the data/raw directory exists."""
    os.makedirs('data/raw', exist_ok=True)

def load_simulation_metadata():
    """Load the simulation metadata JSON."""
    path = 'data/simulation_metadata.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"datasets": {}}

def save_simulation_metadata(metadata: Dict[str, Any]):
    """Save the simulation metadata JSON."""
    with open('data/simulation_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_dataset_checksum(filename: str, expected_checksum: str):
    """Verify a dataset's checksum against the expected value."""
    filepath = os.path.join('data/raw', filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset {filename} not found in data/raw")
    actual = compute_file_checksum(filepath)
    if actual != expected_checksum:
        raise ValueError(f"Checksum mismatch for {filename}: expected {expected_checksum}, got {actual}")

def download_breast_cancer_dataset():
    """Download UCI Breast Cancer (Wisconsin Diagnostic) dataset (ID: 197)."""
    ensure_data_raw_dir()
    filename = 'breast_cancer_wisconsin.csv'
    filepath = os.path.join('data/raw', filename)
    
    if not os.path.exists(filepath):
        dataset = fetch_ucirepo(id=197)
        df = dataset.data.features
        # Add target column if available in features or separate
        if hasattr(dataset.data, 'labels'):
            df['target'] = dataset.data.labels
        df.to_csv(filepath, index=False)
    
    checksum = compute_file_checksum(filepath)
    meta = load_simulation_metadata()
    meta['datasets']['breast_cancer'] = {'id': 197, 'checksum': checksum, 'path': filepath}
    save_simulation_metadata(meta)
    return pd.read_csv(filepath)

def download_wine_dataset():
    """Download UCI Wine dataset (ID: 198)."""
    ensure_data_raw_dir()
    filename = 'wine.csv'
    filepath = os.path.join('data/raw', filename)
    
    if not os.path.exists(filepath):
        dataset = fetch_ucirepo(id=198)
        df = dataset.data.features
        if hasattr(dataset.data, 'labels'):
            df['target'] = dataset.data.labels
        df.to_csv(filepath, index=False)
    
    checksum = compute_file_checksum(filepath)
    meta = load_simulation_metadata()
    meta['datasets']['wine'] = {'id': 198, 'checksum': checksum, 'path': filepath}
    save_simulation_metadata(meta)
    return pd.read_csv(filepath)

def download_adult_dataset():
    """Download UCI Adult (Census Income) dataset (ID: 522)."""
    ensure_data_raw_dir()
    filename = 'adult.csv'
    filepath = os.path.join('data/raw', filename)
    
    if not os.path.exists(filepath):
        dataset = fetch_ucirepo(id=522)
        df = dataset.data.features
        if hasattr(dataset.data, 'labels'):
            df['target'] = dataset.data.labels
        df.to_csv(filepath, index=False)
    
    checksum = compute_file_checksum(filepath)
    meta = load_simulation_metadata()
    meta['datasets']['adult'] = {'id': 522, 'checksum': checksum, 'path': filepath}
    save_simulation_metadata(meta)
    return pd.read_csv(filepath)

def prepare_data_for_ttest(df: pd.DataFrame, target_col: str, group_col: str = None):
    """
    Prepare data for t-test.
    If group_col is provided, splits data by that column.
    Otherwise, splits by target_col if it's binary.
    Returns two arrays: group1, group2
    """
    if group_col:
        groups = df.groupby(group_col)[target_col].apply(list)
        if len(groups) < 2:
            raise ValueError("Need at least two groups for t-test")
        return groups.iloc[0].values, groups.iloc[1].values
    else:
        # Assume target_col is the grouping variable for binary split
        unique_vals = df[target_col].unique()
        if len(unique_vals) < 2:
            raise ValueError("Target column must have at least two unique values for t-test")
        g1 = df[df[target_col] == unique_vals[0]][df.columns[0]].values # Use first numeric col
        g2 = df[df[target_col] == unique_vals[1]][df.columns[0]].values
        return g1, g2

def prepare_data_for_anova(df: pd.DataFrame, target_col: str, group_col: str):
    """
    Prepare data for ANOVA.
    Returns a list of arrays, one for each group.
    """
    groups = df.groupby(group_col)[target_col].apply(list)
    return [g.values for _, g in groups.items()]

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: str, col2: str):
    """
    Prepare data for chi-squared test.
    Returns a contingency table (2D array).
    """
    contingency = pd.crosstab(df[col1], df[col2])
    return contingency.values

def preprocess_dataset_for_validation(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """
    Preprocess a dataset for validation tests.
    Returns a dictionary containing prepared data for t-test, ANOVA, and chi-squared.
    """
    # Select numeric columns for continuous tests
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    result = {}
    
    # For T-Test: Need two groups and one continuous variable
    if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
        group_col = categorical_cols[0]
        target_col = numeric_cols[0]
        try:
            g1, g2 = prepare_data_for_ttest(df, target_col, group_col)
            if len(g1) > 1 and len(g2) > 1:
                result['ttest'] = {'group1': g1, 'group2': g2, 'col1': target_col, 'group_col': group_col}
        except Exception as e:
            pass

    # For ANOVA: Need one grouping variable and one continuous variable with >2 groups
    if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
        group_col = categorical_cols[0]
        target_col = numeric_cols[0]
        try:
            groups = df.groupby(group_col)[target_col].apply(list)
            if len(groups) > 2:
                result['anova'] = {'groups': [g.values for _, g in groups.items()], 'col': target_col, 'group_col': group_col}
        except Exception as e:
            pass

    # For Chi-Squared: Need two categorical variables
    if len(categorical_cols) >= 2:
        try:
            contingency = prepare_data_for_chi_squared(df, categorical_cols[0], categorical_cols[1])
            if contingency.size > 0:
                result['chi_squared'] = {'table': contingency, 'col1': categorical_cols[0], 'col2': categorical_cols[1]}
        except Exception as e:
            pass
    
    return result

def run_validation_tests():
    """
    Run t-test, ANOVA, and chi-squared on real datasets and save observed p-value distributions.
    Output: data/simulation/real_data_pvalues.csv
    """
    datasets = [
        ('breast_cancer', download_breast_cancer_dataset),
        ('wine', download_wine_dataset),
        ('adult', download_adult_dataset)
    ]
    
    results = []
    
    for name, loader in datasets:
        print(f"Processing {name}...")
        df = loader()
        prep = preprocess_dataset_for_validation(df, name)
        
        # Run T-Test
        if 'ttest' in prep:
            data = prep['ttest']
            try:
                stat, p_val = stats.ttest_ind(data['group1'], data['group2'])
                results.append({
                    'dataset': name,
                    'test_type': 't-test',
                    'p_value': p_val,
                    'statistic': stat,
                    'sample_size_1': len(data['group1']),
                    'sample_size_2': len(data['group2'])
                })
            except Exception as e:
                results.append({'dataset': name, 'test_type': 't-test', 'p_value': None, 'error': str(e)})
        
        # Run ANOVA
        if 'anova' in prep:
            data = prep['anova']
            try:
                stat, p_val = stats.f_oneway(*data['groups'])
                results.append({
                    'dataset': name,
                    'test_type': 'anova',
                    'p_value': p_val,
                    'statistic': stat,
                    'num_groups': len(data['groups'])
                })
            except Exception as e:
                results.append({'dataset': name, 'test_type': 'anova', 'p_value': None, 'error': str(e)})
        
        # Run Chi-Squared
        if 'chi_squared' in prep:
            data = prep['chi_squared']
            try:
                stat, p_val, dof, expected = stats.chi2_contingency(data['table'])
                results.append({
                    'dataset': name,
                    'test_type': 'chi-squared',
                    'p_value': p_val,
                    'statistic': stat,
                    'dof': dof
                })
            except Exception as e:
                results.append({'dataset': name, 'test_type': 'chi-squared', 'p_value': None, 'error': str(e)})
    
    # Save results
    output_path = 'data/simulation/real_data_pvalues.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if results:
        df_res = pd.DataFrame(results)
        df_res.to_csv(output_path, index=False)
        print(f"Saved results to {output_path}")
    else:
        print("No valid results to save.")

def main():
    """Main entry point for T031."""
    run_validation_tests()

if __name__ == "__main__":
    main()