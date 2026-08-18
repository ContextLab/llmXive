"""
Validator module for User Story 3: Validation Against Real-World Small-Sample Datasets.

This module handles:
1. Downloading real-world datasets (UCI Breast Cancer, UCI Wine, OpenML Adult).
2. Verifying dataset checksums for data hygiene.
3. Preparing data for statistical tests (t-test, ANOVA, chi-squared).
4. Running statistical tests on real datasets.
5. Saving results to CSV/JSON files.

IMPORTANT DATASET HANDLING NOTES (Constitution Principle III, Large Dataset Rule):
================================================================================
The OpenML Adult dataset (ID 1590) is approximately 300,000+ rows and too large
for the free CI runner (~7GB RAM / ~14GB disk). To handle this:

1. SAMPLING METHOD: We use a FIXED RANDOM SAMPLE of exactly 5,000 rows.
   This provides sufficient statistical power for validation while staying
   within memory constraints.

2. SAMPLING SIZE: 5,000 rows (exact count documented here and in metadata).
   This sample size is large enough to approximate the full distribution
   while being small enough to process in the CI environment.

3. STREAMING: We do NOT use streaming for this dataset because:
   - The statistical tests (t-test, ANOVA, chi-squared) require the full
     contingency table or grouped data to be in memory.
   - Streaming would complicate the aggregation logic significantly.
   - A fixed random sample is statistically valid for validation purposes.

4. DOCUMENTATION: The exact sample size (5000) and method (random sampling
   with fixed seed 42) are documented in:
   - This file (code/analysis/validator.py)
   - data/simulation_metadata.json (via register_dataset_in_metadata)

5. REPRODUCIBILITY: The sampling uses a fixed random seed (42) to ensure
   that the same 5,000 rows are selected on every run.

See also: T041 task description for explicit documentation requirements.
"""

import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import warnings

# Import from simulation module
from code.simulation.logging_config import get_logger, log_operation
from code.simulation import get_rng
from code.utils.checksum_utils import (
    ensure_metadata_file_exists,
    load_simulation_metadata,
    save_simulation_metadata,
    compute_file_checksum,
    register_dataset_checksum
)

logger = get_logger(__name__)

# Constants for OpenML Adult dataset handling
# T041: Explicitly documenting sample size and sampling method
ADULT_DATASET_ID = 1590
ADULT_SAMPLE_SIZE = 5000  # Fixed sample size for CI runner constraints
ADULT_RANDOM_SEED = 42    # Fixed seed for reproducibility

def ensure_data_raw_dir() -> str:
    """Ensure the data/raw directory exists."""
    raw_dir = "data/raw"
    os.makedirs(raw_dir, exist_ok=True)
    return raw_dir

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hex digest of the file checksum
    """
    hasher = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def register_dataset_checksum(dataset_name: str, filepath: str, metadata_file: str = "data/simulation_metadata.json") -> None:
    """
    Register a dataset checksum in the simulation metadata.

    Args:
        dataset_name: Name of the dataset
        filepath: Path to the dataset file
        metadata_file: Path to the metadata JSON file
    """
    checksum = compute_file_checksum(filepath)
    register_dataset_checksum(dataset_name, checksum, metadata_file)
    logger.log_operation("dataset_checksum_registered", dataset=dataset_name, checksum=checksum)

def download_breast_cancer_dataset() -> pd.DataFrame:
    """
    Download the UCI Breast Cancer (Wisconsin Diagnostic) dataset.

    Uses ucimlrepo with dataset ID 197.

    Returns:
        DataFrame containing the dataset
    """
    try:
        from ucimlrepo import fetch_ucirepo
        breast_cancer = fetch_ucirepo(id=197)
        df = breast_cancer.data.features
        target = breast_cancer.data.targets
        if target is not None:
            df['target'] = target.iloc[:, 0]
        logger.log_operation("dataset_downloaded", dataset="breast_cancer", id=197, rows=len(df))
        return df
    except ImportError:
        raise RuntimeError("ucimlrepo package not installed. Please run: pip install ucimlrepo")
    except Exception as e:
        raise RuntimeError(f"Failed to download Breast Cancer dataset (ID 197): {str(e)}")

def download_wine_dataset() -> pd.DataFrame:
    """
    Download the UCI Wine dataset.

    Uses ucimlrepo with dataset ID 198.

    Returns:
        DataFrame containing the dataset
    """
    try:
        from ucimlrepo import fetch_ucirepo
        wine = fetch_ucirepo(id=198)
        df = wine.data.features
        target = wine.data.targets
        if target is not None:
            df['target'] = target.iloc[:, 0]
        logger.log_operation("dataset_downloaded", dataset="wine", id=198, rows=len(df))
        return df
    except ImportError:
        raise RuntimeError("ucimlrepo package not installed. Please run: pip install ucimlrepo")
    except Exception as e:
        raise RuntimeError(f"Failed to download Wine dataset (ID 198): {str(e)}")

def download_adult_dataset() -> pd.DataFrame:
    """
    Download the OpenML Adult dataset.

    Uses openml library with dataset ID 1590.

    IMPORTANT: The full Adult dataset is too large for the free CI runner.
    We use a FIXED RANDOM SAMPLE of 5,000 rows (T041 documentation requirement).

    Sampling Method:
    - Random sampling with replacement=False
    - Fixed random seed: 42
    - Sample size: 5,000 rows (exact count documented)

    This sample size is sufficient for statistical validation while staying
    within memory constraints (~7GB RAM limit).

    Returns:
        DataFrame containing the sampled dataset
    """
    try:
        import openml
        from openml.datasets import OpenMLDataset

        # Set random seed for reproducibility
        rng = get_rng(ADULT_RANDOM_SEED)

        # Download the dataset
        logger.log_operation("dataset_fetch_start", dataset="adult", id=ADULT_DATASET_ID)
        dataset = openml.datasets.get_dataset(ADULT_DATASET_ID)

        # Download the data
        X, y, categorical_indicator, attribute_names = dataset.get_data(
            dataset_format="dataframe",
            target=dataset.default_target_attribute
        )

        logger.log_operation("dataset_fetched_full", dataset="adult", full_rows=len(X))

        # T041: Apply fixed random sampling due to dataset size constraints
        # The full dataset has ~300,000+ rows which exceeds CI memory limits.
        # We use a fixed sample of 5,000 rows for validation.
        if len(X) > ADULT_SAMPLE_SIZE:
            logger.log_operation(
                "dataset_sampling_applied",
                dataset="adult",
                full_rows=len(X),
                sample_size=ADULT_SAMPLE_SIZE,
                method="random_sampling_fixed_seed",
                seed=ADULT_RANDOM_SEED,
                reason="CI runner memory constraints (T041)"
            )
            # Get random indices without replacement
            sample_indices = rng.choice(len(X), size=ADULT_SAMPLE_SIZE, replace=False)
            X_sample = X.iloc[sample_indices].reset_index(drop=True)
            y_sample = y.iloc[sample_indices].reset_index(drop=True)
            X_final = pd.concat([X_sample, y_sample], axis=1)
            X_final.columns = list(attribute_names) + [dataset.default_target_attribute]
        else:
            # If dataset is smaller than sample size, use all data
            X_final = pd.concat([X, y], axis=1)
            X_final.columns = list(attribute_names) + [dataset.default_target_attribute]

        logger.log_operation(
            "dataset_downloaded",
            dataset="adult",
            id=ADULT_DATASET_ID,
            rows=len(X_final),
            sample_method="random_sampling",
            sample_size=ADULT_SAMPLE_SIZE,
            seed=ADULT_RANDOM_SEED,
            note="T041: Fixed sample size documented for CI constraints"
        )

        return X_final

    except ImportError:
        raise RuntimeError("openml package not installed. Please run: pip install openml")
    except Exception as e:
        raise RuntimeError(f"Failed to download Adult dataset (ID {ADULT_DATASET_ID}): {str(e)}")

def verify_dataset_checksum(dataset_name: str, filepath: str, metadata_file: str = "data/simulation_metadata.json") -> bool:
    """
    Verify a dataset's checksum against the stored value.

    Args:
        dataset_name: Name of the dataset
        filepath: Path to the dataset file
        metadata_file: Path to the metadata JSON file

    Returns:
        True if checksum matches, False otherwise
    """
    metadata = load_simulation_metadata(metadata_file)
    if dataset_name not in metadata.get("checksums", {}):
        logger.log_operation("checksum_not_found", dataset=dataset_name)
        return False

    stored_checksum = metadata["checksums"][dataset_name]
    actual_checksum = compute_file_checksum(filepath)

    if stored_checksum != actual_checksum:
        logger.log_operation(
            "checksum_mismatch",
            dataset=dataset_name,
            stored=stored_checksum,
            actual=actual_checksum
        )
        return False

    logger.log_operation("checksum_verified", dataset=dataset_name)
    return True

def register_dataset_in_metadata(
    dataset_name: str,
    filepath: str,
    rows: int,
    sample_method: Optional[str] = None,
    sample_size: Optional[int] = None,
    seed: Optional[int] = None,
    metadata_file: str = "data/simulation_metadata.json"
) -> None:
    """
    Register dataset information in the simulation metadata.

    Args:
        dataset_name: Name of the dataset
        filepath: Path to the dataset file
        rows: Number of rows in the dataset
        sample_method: Method used for sampling (if applicable)
        sample_size: Sample size used (if applicable)
        seed: Random seed used (if applicable)
        metadata_file: Path to the metadata JSON file
    """
    metadata = load_simulation_metadata(metadata_file)

    checksum = compute_file_checksum(filepath)

    dataset_info = {
        "filepath": filepath,
        "rows": rows,
        "checksum": checksum,
        "timestamp": pd.Timestamp.now().isoformat()
    }

    # T041: Document sample size and sampling method for OpenML Adult
    if sample_method is not None:
        dataset_info["sample_method"] = sample_method
    if sample_size is not None:
        dataset_info["sample_size"] = sample_size
    if seed is not None:
        dataset_info["random_seed"] = seed

    metadata["datasets"] = metadata.get("datasets", {})
    metadata["datasets"][dataset_name] = dataset_info

    save_simulation_metadata(metadata, metadata_file)
    logger.log_operation(
        "dataset_registered",
        dataset=dataset_name,
        rows=rows,
        sample_method=sample_method,
        sample_size=sample_size,
        seed=seed
    )

def prepare_data_for_ttest(df: pd.DataFrame, target_col: str, feature_col: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare data for a two-sample t-test.

    Args:
        df: DataFrame containing the data
        target_col: Name of the target/categorical column
        feature_col: Name of the feature/numerical column

    Returns:
        Tuple of (group1_values, group2_values)
    """
    groups = df.groupby(target_col)[feature_col]
    group_names = list(groups.groups.keys())

    if len(group_names) < 2:
        raise ValueError(f"Need at least 2 groups for t-test, found {len(group_names)}")

    group1 = groups.get_group(group_names[0]).values
    group2 = groups.get_group(group_names[1]).values

    return group1, group2

def prepare_data_for_anova(df: pd.DataFrame, target_col: str, feature_col: str) -> List[np.ndarray]:
    """
    Prepare data for ANOVA test.

    Args:
        df: DataFrame containing the data
        target_col: Name of the target/categorical column
        feature_col: Name of the feature/numerical column

    Returns:
        List of arrays, one for each group
    """
    groups = df.groupby(target_col)[feature_col]
    return [group.values for _, group in groups]

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: str, col2: str) -> np.ndarray:
    """
    Prepare data for chi-squared test of independence.

    Args:
        df: DataFrame containing the data
        col1: Name of the first categorical column
        col2: Name of the second categorical column

    Returns:
        Contingency table as a numpy array
    """
    contingency = pd.crosstab(df[col1], df[col2])
    return contingency.values

def run_t_test(df: pd.DataFrame, target_col: str, feature_col: str) -> Dict[str, Any]:
    """
    Run a two-sample t-test on the data.

    Args:
        df: DataFrame containing the data
        target_col: Name of the target/categorical column
        feature_col: Name of the feature/numerical column

    Returns:
        Dictionary with test results
    """
    group1, group2 = prepare_data_for_ttest(df, target_col, feature_col)

    # Use Welch's t-test (unequal variance) by default
    statistic, p_value = stats.ttest_ind(group1, group2, equal_var=False)

    return {
        "test_type": "t-test",
        "p_value": p_value,
        "statistic": statistic,
        "group1_size": len(group1),
        "group2_size": len(group2)
    }

def run_anova(df: pd.DataFrame, target_col: str, feature_col: str) -> Dict[str, Any]:
    """
    Run ANOVA test on the data.

    Args:
        df: DataFrame containing the data
        target_col: Name of the target/categorical column
        feature_col: Name of the feature/numerical column

    Returns:
        Dictionary with test results
    """
    groups = prepare_data_for_anova(df, target_col, feature_col)

    if len(groups) < 2:
        raise ValueError("ANOVA requires at least 2 groups")

    statistic, p_value = stats.f_oneway(*groups)

    return {
        "test_type": "anova",
        "p_value": p_value,
        "statistic": statistic,
        "num_groups": len(groups),
        "group_sizes": [len(g) for g in groups]
    }

def run_chi_squared(df: pd.DataFrame, col1: str, col2: str) -> Dict[str, Any]:
    """
    Run chi-squared test of independence.

    Args:
        df: DataFrame containing the data
        col1: Name of the first categorical column
        col2: Name of the second categorical column

    Returns:
        Dictionary with test results
    """
    contingency = prepare_data_for_chi_squared(df, col1, col2)

    statistic, p_value, dof, expected = stats.chi2_contingency(contingency)

    return {
        "test_type": "chi-squared",
        "p_value": p_value,
        "statistic": statistic,
        "dof": dof,
        "expected_counts": expected.tolist()
    }

def run_validation_on_datasets(
    datasets: Dict[str, pd.DataFrame],
    test_configs: Dict[str, Tuple[str, str]]
) -> List[Dict[str, Any]]:
    """
    Run statistical tests on multiple datasets.

    Args:
        datasets: Dictionary of dataset_name -> DataFrame
        test_configs: Dictionary of test_name -> (col1, col2) or (target, feature)

    Returns:
        List of test result dictionaries
    """
    results = []

    for dataset_name, df in datasets.items():
        for test_name, config in test_configs.items():
            try:
                if test_name == "t-test":
                    target_col, feature_col = config
                    result = run_t_test(df, target_col, feature_col)
                elif test_name == "anova":
                    target_col, feature_col = config
                    result = run_anova(df, target_col, feature_col)
                elif test_name == "chi-squared":
                    col1, col2 = config
                    result = run_chi_squared(df, col1, col2)
                else:
                    continue

                result["dataset_id"] = dataset_name
                results.append(result)
            except Exception as e:
                logger.log_operation(
                    "test_failed",
                    dataset=dataset_name,
                    test=test_name,
                    error=str(e)
                )
                results.append({
                    "dataset_id": dataset_name,
                    "test_type": test_name,
                    "p_value": None,
                    "error": str(e)
                })

    return results

def save_p_values_to_csv(results: List[Dict[str, Any]], filepath: str = "data/simulation/real_data_pvalues.csv") -> None:
    """
    Save p-values to a CSV file.

    Args:
        results: List of test result dictionaries
        filepath: Output file path
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    df_results = pd.DataFrame(results)
    df_results.to_csv(filepath, index=False)

    logger.log_operation("pvalues_saved", filepath=filepath, rows=len(df_results))

def load_p_values_to_csv_safe(filepath: str = "data/simulation/real_data_pvalues.csv") -> pd.DataFrame:
    """
    Load p-values from a CSV file safely.

    Args:
        filepath: Input file path

    Returns:
        DataFrame with p-values
    """
    if not os.path.exists(filepath):
        logger.log_operation("pvalues_file_not_found", filepath=filepath)
        return pd.DataFrame()

    return pd.read_csv(filepath)

def main():
    """
    Main function to run the validation pipeline.

    This function:
    1. Downloads all three datasets (Breast Cancer, Wine, Adult)
    2. Registers checksums in metadata
    3. Runs statistical tests on each dataset
    4. Saves results to CSV
    """
    logger.log_operation("validation_pipeline_start")

    # Ensure data directories exist
    ensure_data_raw_dir()

    # Download datasets
    datasets = {}

    # Breast Cancer
    try:
        breast_df = download_breast_cancer_dataset()
        datasets["breast_cancer_197"] = breast_df
        # Save to file for checksum
        breast_path = "data/raw/breast_cancer_197.csv"
        breast_df.to_csv(breast_path, index=False)
        register_dataset_checksum("breast_cancer_197", breast_path)
        register_dataset_in_metadata("breast_cancer_197", breast_path, len(breast_df))
    except Exception as e:
        logger.log_operation("validation_error", dataset="breast_cancer", error=str(e))

    # Wine
    try:
        wine_df = download_wine_dataset()
        datasets["wine_198"] = wine_df
        wine_path = "data/raw/wine_198.csv"
        wine_df.to_csv(wine_path, index=False)
        register_dataset_checksum("wine_198", wine_path)
        register_dataset_in_metadata("wine_198", wine_path, len(wine_df))
    except Exception as e:
        logger.log_operation("validation_error", dataset="wine", error=str(e))

    # Adult (OpenML) - T041: Documented sampling method
    try:
        adult_df = download_adult_dataset()
        datasets["adult_1590"] = adult_df
        adult_path = "data/raw/adult_1590.csv"
        adult_df.to_csv(adult_path, index=False)
        register_dataset_checksum("adult_1590", adult_path)
        # T041: Register with sampling documentation
        register_dataset_in_metadata(
            "adult_1590",
            adult_path,
            len(adult_df),
            sample_method="random_sampling",
            sample_size=ADULT_SAMPLE_SIZE,
            seed=ADULT_RANDOM_SEED
        )
    except Exception as e:
        logger.log_operation("validation_error", dataset="adult", error=str(e))

    if not datasets:
        raise RuntimeError("No datasets were successfully downloaded")

    # Define test configurations for each dataset
    # These are example configurations - adjust based on actual dataset structure
    test_configs = {
        "t-test": ("target", "mean_radius"),  # Breast Cancer example
        "anova": ("target", "mean_radius"),   # Breast Cancer example
        "chi-squared": ("target", "diagnosis")  # Breast Cancer example
    }

    # Adjust configs for Wine dataset (different structure)
    wine_configs = {
        "t-test": ("target", "alcohol"),
        "anova": ("target", "alcohol"),
        "chi-squared": ("target", "color_intensity")
    }

    # Adjust configs for Adult dataset (different structure)
    adult_configs = {
        "t-test": ("class", "age"),
        "anova": ("class", "age"),
        "chi-squared": ("class", "education")
    }

    all_results = []

    # Run tests on Breast Cancer
    if "breast_cancer_197" in datasets:
        results = run_validation_on_datasets(
            {"breast_cancer_197": datasets["breast_cancer_197"]},
            test_configs
        )
        all_results.extend(results)

    # Run tests on Wine
    if "wine_198" in datasets:
        results = run_validation_on_datasets(
            {"wine_198": datasets["wine_198"]},
            wine_configs
        )
        all_results.extend(results)

    # Run tests on Adult
    if "adult_1590" in datasets:
        results = run_validation_on_datasets(
            {"adult_1590": datasets["adult_1590"]},
            adult_configs
        )
        all_results.extend(results)

    # Save results
    save_p_values_to_csv(all_results)

    logger.log_operation("validation_pipeline_complete", total_tests=len(all_results))

    return all_results

if __name__ == "__main__":
    main()