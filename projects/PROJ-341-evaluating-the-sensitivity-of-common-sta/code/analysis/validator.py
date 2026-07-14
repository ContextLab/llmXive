"""
Validator module for real-world dataset validation.
Downloads UCI datasets, verifies checksums, and runs statistical tests.
"""
import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import warnings

from code.simulation.logging_config import (
    get_logger, log_output_file_written, log_error_details,
    log_fallback_triggered, log_warning_assumption_violated
)

# Import from sibling modules
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation.test_runner import run_t_test, run_anova

# Initialize logger
_logger = get_logger("analysis.validator")

def ensure_data_raw_dir() -> str:
    """Ensure the data/raw directory exists."""
    data_raw_dir = "data/raw"
    os.makedirs(data_raw_dir, exist_ok=True)
    _logger.info(f"Ensured data/raw directory exists: {data_raw_dir}")
    return data_raw_dir

def load_simulation_metadata() -> Dict[str, Any]:
    """Load simulation metadata from JSON file."""
    metadata_path = "data/simulation_metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        _logger.info(f"Loaded simulation metadata from {metadata_path}")
        return metadata
    else:
        _logger.warning(f"Metadata file not found: {metadata_path}. Creating new.")
        return {"datasets": {}, "checksums": {}, "seeds": []}

def save_simulation_metadata(metadata: Dict[str, Any]) -> None:
    """Save simulation metadata to JSON file."""
    metadata_path = "data/simulation_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    _logger.info(f"Saved simulation metadata to {metadata_path}")

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
    
    Returns:
        Hex digest of the file checksum
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    checksum = hash_func.hexdigest()
    _logger.debug(f"Computed checksum for {file_path}: {checksum}")
    return checksum

def verify_dataset_checksum(dataset_name: str, file_path: str, expected_checksum: str) -> bool:
    """
    Verify dataset checksum against expected value.
    
    Args:
        dataset_name: Name of the dataset
        file_path: Path to the dataset file
        expected_checksum: Expected checksum value
    
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = compute_file_checksum(file_path)
    if actual_checksum == expected_checksum:
        _logger.info(f"Checksum verified for {dataset_name}: {actual_checksum}")
        return True
    else:
        _logger.error(f"Checksum mismatch for {dataset_name}! Expected: {expected_checksum}, Got: {actual_checksum}")
        return False

def download_breast_cancer_dataset() -> pd.DataFrame:
    """
    Download UCI Breast Cancer (Wisconsin Diagnostic) dataset.
    
    Returns:
        DataFrame with the dataset
    """
    _logger.info("Downloading UCI Breast Cancer dataset...")
    try:
        from ucimlrepo import fetch_ucirepo
        breast_cancer = fetch_ucirepo(id=197)
        df = breast_cancer.data.features
        df['target'] = breast_cancer.data.targets['diagnosis']
        _logger.info(f"Downloaded Breast Cancer dataset: {df.shape}")
        return df
    except Exception as e:
        log_error_details(e, "download_breast_cancer_dataset", _logger)
        raise

def download_wine_dataset() -> pd.DataFrame:
    """
    Download UCI Wine dataset.
    
    Returns:
        DataFrame with the dataset
    """
    _logger.info("Downloading UCI Wine dataset...")
    try:
        from ucimlrepo import fetch_ucirepo
        wine = fetch_ucirepo(id=198)
        df = wine.data.features
        df['target'] = wine.data.targets['class']
        _logger.info(f"Downloaded Wine dataset: {df.shape}")
        return df
    except Exception as e:
        log_error_details(e, "download_wine_dataset", _logger)
        raise

def download_adult_dataset() -> pd.DataFrame:
    """
    Download UCI Adult (Census Income) dataset.
    
    Returns:
        DataFrame with the dataset
    """
    _logger.info("Downloading UCI Adult dataset...")
    try:
        from ucimlrepo import fetch_ucirepo
        adult = fetch_ucirepo(id=522)
        df = adult.data.features
        df['target'] = adult.data.targets['income']
        _logger.info(f"Downloaded Adult dataset: {df.shape}")
        return df
    except Exception as e:
        log_error_details(e, "download_adult_dataset", _logger)
        raise

def run_checksum_verification(datasets: Dict[str, str], metadata: Dict[str, Any]) -> Dict[str, bool]:
    """
    Run checksum verification for all datasets.
    
    Args:
        datasets: Dictionary mapping dataset names to file paths
        metadata: Simulation metadata containing expected checksums
    
    Returns:
        Dictionary mapping dataset names to verification results
    """
    results = {}
    for name, path in datasets.items():
        if name in metadata.get('checksums', {}):
            expected = metadata['checksums'][name]
            results[name] = verify_dataset_checksum(name, path, expected)
        else:
            _logger.warning(f"No checksum found for {name} in metadata. Skipping verification.")
            results[name] = True  # Skip if no expected checksum
    return results

def prepare_data_for_ttest(df: pd.DataFrame, feature_col: str, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare data for t-test.
    
    Args:
        df: DataFrame
        feature_col: Feature column name
        target_col: Target column name (binary)
    
    Returns:
        Tuple of (group1, group2) arrays
    """
    _logger.debug(f"Preparing data for t-test: feature={feature_col}, target={target_col}")
    groups = df.groupby(target_col)[feature_col]
    if len(groups) != 2:
        raise ValueError(f"Target column {target_col} must have exactly 2 unique values for t-test")
    group1 = groups.get_group(groups.groups.keys()[0]).values
    group2 = groups.get_group(groups.groups.keys()[1]).values
    _logger.debug(f"T-test groups: n1={len(group1)}, n2={len(group2)}")
    return group1, group2

def prepare_data_for_anova(df: pd.DataFrame, feature_col: str, target_col: str) -> List[np.ndarray]:
    """
    Prepare data for ANOVA.
    
    Args:
        df: DataFrame
        feature_col: Feature column name
        target_col: Target column name (categorical)
    
    Returns:
        List of arrays for each group
    """
    _logger.debug(f"Preparing data for ANOVA: feature={feature_col}, target={target_col}")
    groups = df.groupby(target_col)[feature_col]
    group_arrays = [group.values for _, group in groups]
    _logger.debug(f"ANOVA groups: {len(group_arrays)} groups")
    return group_arrays

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: str, col2: str) -> np.ndarray:
    """
    Prepare data for chi-squared test.
    
    Args:
        df: DataFrame
        col1: First categorical column
        col2: Second categorical column
    
    Returns:
        Contingency table as numpy array
    """
    _logger.debug(f"Preparing data for chi-squared: col1={col1}, col2={col2}")
    contingency = pd.crosstab(df[col1], df[col2]).values
    _logger.debug(f"Chi-squared contingency table shape: {contingency.shape}")
    return contingency

def preprocess_dataset_for_validation(
    df: pd.DataFrame,
    dataset_name: str,
    test_type: str
) -> Dict[str, Any]:
    """
    Preprocess dataset for validation tests.
    
    Args:
        df: DataFrame
        dataset_name: Name of the dataset
        test_type: Type of test ('t-test', 'anova', 'chi-squared')
    
    Returns:
        Dictionary with prepared data
    """
    _logger.info(f"Preprocessing {dataset_name} for {test_type}")
    
    if test_type == 't-test':
        # Select a numeric feature and binary target
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            _logger.warning(f"Not enough numeric columns in {dataset_name} for t-test")
            return {}
        
        feature_col = numeric_cols[0]
        target_col = numeric_cols[1] if len(numeric_cols) > 1 else 'target'
        
        # Ensure target is binary
        if df[target_col].nunique() != 2:
            # Try to create a binary target
            median_val = df[numeric_cols[-1]].median()
            df['binary_target'] = (df[numeric_cols[-1]] > median_val).astype(int)
            target_col = 'binary_target'
        
        group1, group2 = prepare_data_for_ttest(df, feature_col, target_col)
        return {'group1': group1, 'group2': group2}
    
    elif test_type == 'anova':
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(categorical_cols) == 0:
            # Create a categorical variable from median split
            median_val = df[numeric_cols[0]].median()
            df['category'] = (df[numeric_cols[0]] > median_val).astype(int)
            categorical_cols = ['category']
        
        feature_col = numeric_cols[0]
        target_col = categorical_cols[0]
        groups = prepare_data_for_anova(df, feature_col, target_col)
        return {'groups': groups}
    
    elif test_type == 'chi-squared':
        categorical_cols = df.select_dtypes(include=['object', 'category', 'int']).columns
        if len(categorical_cols) < 2:
            _logger.warning(f"Not enough categorical columns in {dataset_name} for chi-squared")
            return {}
        
        col1 = categorical_cols[0]
        col2 = categorical_cols[1]
        contingency = prepare_data_for_chi_squared(df, col1, col2)
        return {'contingency': contingency}
    
    else:
        raise ValueError(f"Unknown test type: {test_type}")

def run_validation_tests(
    df: pd.DataFrame,
    dataset_name: str,
    test_types: List[str] = ['t-test', 'anova', 'chi-squared']
) -> List[Dict[str, Any]]:
    """
    Run all specified validation tests on a dataset.
    
    Args:
        df: DataFrame
        dataset_name: Name of the dataset
        test_types: List of test types to run
    
    Returns:
        List of test results
    """
    results = []
    
    for test_type in test_types:
        try:
            _logger.info(f"Running {test_type} on {dataset_name}")
            prepared_data = preprocess_dataset_for_validation(df, dataset_name, test_type)
            
            if not prepared_data:
                _logger.warning(f"No data prepared for {test_type} on {dataset_name}")
                continue
            
            if test_type == 't-test':
                stat, p_value = run_t_test(prepared_data['group1'], prepared_data['group2'])
                results.append({
                    'dataset': dataset_name,
                    'test': 't-test',
                    'statistic': stat,
                    'p_value': p_value,
                    'sample_sizes': [len(prepared_data['group1']), len(prepared_data['group2'])]
                })
                _logger.debug(f"T-test result: p={p_value:.6f}")
            
            elif test_type == 'anova':
                stat, p_value = run_anova(*prepared_data['groups'])
                results.append({
                    'dataset': dataset_name,
                    'test': 'anova',
                    'statistic': stat,
                    'p_value': p_value,
                    'groups': len(prepared_data['groups'])
                })
                _logger.debug(f"ANOVA result: p={p_value:.6f}")
            
            elif test_type == 'chi-squared':
                contingency = prepared_data['contingency']
                stat, p_value, dof, expected = run_chi_squared_with_fallback(contingency)
                results.append({
                    'dataset': dataset_name,
                    'test': 'chi-squared',
                    'statistic': stat,
                    'p_value': p_value,
                    'degrees_of_freedom': dof,
                    'table_shape': contingency.shape
                })
                _logger.debug(f"Chi-squared result: p={p_value:.6f}")
        
        except Exception as e:
            log_error_details(e, f"run_validation_tests:{test_type}", _logger)
            results.append({
                'dataset': dataset_name,
                'test': test_type,
                'error': str(e)
            })
    
    return results

def main():
    """Main entry point for validation."""
    _logger.info("Starting validation process")
    
    try:
        # Ensure directories
        ensure_data_raw_dir()
        metadata = load_simulation_metadata()
        
        # Download datasets
        datasets = {
            'breast_cancer': download_breast_cancer_dataset(),
            'wine': download_wine_dataset(),
            'adult': download_adult_dataset()
        }
        
        # Compute and save checksums
        checksums = {}
        for name, df in datasets.items():
            # Save to CSV for checksum
            csv_path = f"data/raw/{name}.csv"
            df.to_csv(csv_path, index=False)
            checksum = compute_file_checksum(csv_path)
            checksums[name] = checksum
            metadata['checksums'][name] = checksum
        
        save_simulation_metadata(metadata)
        _logger.info("Checksums computed and saved")
        
        # Run validation tests
        all_results = []
        for name, df in datasets.items():
            results = run_validation_tests(df, name)
            all_results.extend(results)
        
        # Save results
        output_path = "data/simulation/real_data_pvalues.csv"
        import csv
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_results[0].keys() if all_results else [])
            writer.writeheader()
            writer.writerows(all_results)
        
        log_output_file_written(output_path, len(all_results), _logger)
        _logger.info(f"Validation complete. Results saved to {output_path}")
        
    except Exception as e:
        log_error_details(e, "main", _logger)
        raise

if __name__ == "__main__":
    main()
