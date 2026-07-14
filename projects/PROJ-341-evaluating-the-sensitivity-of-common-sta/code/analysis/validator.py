import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
from ucimlrepo import fetch_ucirepo
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation.test_runner import run_t_test, run_anova
from code.simulation.output_writer import write_p_values_raw

def ensure_data_raw_dir():
    """Ensure the data/raw directory exists."""
    os.makedirs("data/raw", exist_ok=True)

def load_simulation_metadata():
    """Load simulation metadata from JSON file."""
    metadata_path = "data/simulation_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            return json.load(f)
    return {"datasets": {}, "seeds": [], "config": {}}

def save_simulation_metadata(metadata):
    """Save simulation metadata to JSON file."""
    metadata_path = "data/simulation_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

def compute_file_checksum(filepath):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_dataset_checksum(metadata, dataset_name):
    """Verify checksum of a dataset against stored metadata."""
    if dataset_name not in metadata.get("datasets", {}):
        return False
    stored_checksum = metadata["datasets"][dataset_name].get("checksum")
    if not stored_checksum:
        return False
    
    # Find the file path for this dataset
    # Assuming datasets are stored in data/raw/ with specific naming
    file_path = f"data/raw/{dataset_name}.csv"
    if not os.path.exists(file_path):
        return False
    
    current_checksum = compute_file_checksum(file_path)
    return current_checksum == stored_checksum

def download_breast_cancer_dataset():
    """Download UCI Breast Cancer (Wisconsin Diagnostic) dataset."""
    try:
        # Dataset ID 197: Breast Cancer Wisconsin (Diagnostic)
        breast_cancer = fetch_ucirepo(id=197)
        df = breast_cancer.data.features
        target = breast_cancer.data.targets
        
        # Combine features and target
        df['target'] = target['diagnosis']
        df.to_csv("data/raw/breast_cancer.csv", index=False)
        
        checksum = compute_file_checksum("data/raw/breast_cancer.csv")
        return df, checksum
    except Exception as e:
        raise RuntimeError(f"Failed to download breast cancer dataset: {e}")

def download_wine_dataset():
    """Download UCI Wine dataset."""
    try:
        # Dataset ID 198: Wine
        wine = fetch_ucirepo(id=198)
        df = wine.data.features
        target = wine.data.targets
        
        df['target'] = target['class']
        df.to_csv("data/raw/wine.csv", index=False)
        
        checksum = compute_file_checksum("data/raw/wine.csv")
        return df, checksum
    except Exception as e:
        raise RuntimeError(f"Failed to download wine dataset: {e}")

def download_adult_dataset():
    """Download UCI Adult (Census Income) dataset."""
    try:
        # Dataset ID 522: Adult
        adult = fetch_ucirepo(id=522)
        df = adult.data.features
        target = adult.data.targets
        
        df['target'] = target['class']
        df.to_csv("data/raw/adult.csv", index=False)
        
        checksum = compute_file_checksum("data/raw/adult.csv")
        return df, checksum
    except Exception as e:
        raise RuntimeError(f"Failed to download adult dataset: {e}")

def save_dataset_to_csv(df, filename):
    """Save a pandas DataFrame to CSV."""
    os.makedirs("data/raw", exist_ok=True)
    filepath = f"data/raw/{filename}"
    df.to_csv(filepath, index=False)
    return filepath

def verify_dataset_integrity(df, dataset_name, expected_min_rows=10):
    """Verify basic integrity of a dataset."""
    if len(df) < expected_min_rows:
        raise ValueError(f"Dataset {dataset_name} has fewer than {expected_min_rows} rows")
    return True

def prepare_data_for_ttest(df, target_col, group_col, numeric_col):
    """Prepare data for t-test by splitting into groups."""
    groups = df.groupby(group_col)[numeric_col].apply(list).to_dict()
    if len(groups) != 2:
        raise ValueError("T-test requires exactly two groups")
    return list(groups.values())

def prepare_data_for_anova(df, target_col, group_col, numeric_col):
    """Prepare data for ANOVA by splitting into multiple groups."""
    groups = df.groupby(group_col)[numeric_col].apply(list).to_dict()
    if len(groups) < 2:
        raise ValueError("ANOVA requires at least two groups")
    return list(groups.values())

def prepare_data_for_chi_squared(df, row_col, col_col):
    """Prepare data for chi-squared test by creating contingency table."""
    contingency = pd.crosstab(df[row_col], df[col_col])
    return contingency.values

def preprocess_dataset_for_validation(df, dataset_name):
    """Preprocess dataset for validation tests."""
    # Clean data: remove rows with missing values
    df = df.dropna()
    
    # Convert categorical columns to numeric where needed
    for col in df.select_dtypes(include=['object']).columns:
        if col != 'target':
            df[col] = df[col].astype('category').cat.codes
    
    return df

def run_validation_tests():
    """Run t-test, ANOVA, and chi-squared on real datasets and save results."""
    datasets = [
        ("breast_cancer", download_breast_cancer_dataset, "target", "radius_mean", "texture_mean"),
        ("wine", download_wine_dataset, "target", "alcohol", "malic_acid"),
        ("adult", download_adult_dataset, "target", "age", "education_num")
    ]
    
    results = []
    
    for dataset_name, download_func, target_col, numeric_col1, numeric_col2 in datasets:
        try:
            df, checksum = download_func()
            df = preprocess_dataset_for_validation(df, dataset_name)
            
            # Verify dataset integrity
            verify_dataset_integrity(df, dataset_name)
            
            # Update metadata with checksum
            metadata = load_simulation_metadata()
            metadata["datasets"][dataset_name] = {
                "checksum": checksum,
                "rows": len(df),
                "columns": list(df.columns)
            }
            save_simulation_metadata(metadata)
            
            # T-test: Compare two groups based on target
            # For breast cancer: M vs B
            # For wine: class 0 vs 1
            # For adult: <=50K vs >50K
            try:
                groups = prepare_data_for_ttest(df, target_col, target_col, numeric_col1)
                t_stat, p_value = run_t_test(groups[0], groups[1])
                results.append({
                    "dataset": dataset_name,
                    "test": "t_test",
                    "feature": numeric_col1,
                    "p_value": p_value,
                    "statistic": t_stat
                })
            except Exception as e:
                results.append({
                    "dataset": dataset_name,
                    "test": "t_test",
                    "feature": numeric_col1,
                    "p_value": None,
                    "error": str(e)
                })
            
            # ANOVA: Compare multiple groups
            try:
                groups = prepare_data_for_anova(df, target_col, target_col, numeric_col1)
                f_stat, p_value = run_anova(groups)
                results.append({
                    "dataset": dataset_name,
                    "test": "anova",
                    "feature": numeric_col1,
                    "p_value": p_value,
                    "statistic": f_stat
                })
            except Exception as e:
                results.append({
                    "dataset": dataset_name,
                    "test": "anova",
                    "feature": numeric_col1,
                    "p_value": None,
                    "error": str(e)
                })
            
            # Chi-squared: For categorical data
            # Use target and a categorical feature if available
            categorical_cols = df.select_dtypes(include=['category', 'object']).columns
            if len(categorical_cols) >= 2:
                row_col = categorical_cols[0]
                col_col = categorical_cols[1]
                try:
                    contingency = prepare_data_for_chi_squared(df, row_col, col_col)
                    chi_stat, p_value, dof, expected = run_chi_squared_with_fallback(contingency)
                    results.append({
                        "dataset": dataset_name,
                        "test": "chi_squared",
                        "row_feature": row_col,
                        "col_feature": col_col,
                        "p_value": p_value,
                        "statistic": chi_stat
                    })
                except Exception as e:
                    results.append({
                        "dataset": dataset_name,
                        "test": "chi_squared",
                        "row_feature": row_col,
                        "col_feature": col_col,
                        "p_value": None,
                        "error": str(e)
                    })
            
        except Exception as e:
            print(f"Error processing {dataset_name}: {e}")
            continue
    
    # Save results to CSV
    output_path = "data/simulation/real_data_pvalues.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write results to CSV
    if results:
        df_results = pd.DataFrame(results)
        df_results.to_csv(output_path, index=False)
        print(f"Saved p-values to {output_path}")
    else:
        print("No results to save")
    
    return results

def main():
    """Main entry point for validation tests."""
    print("Running validation tests on real datasets...")
    results = run_validation_tests()
    print(f"Completed. Found {len(results)} test results.")
    return results

if __name__ == "__main__":
    main()