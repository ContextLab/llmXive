import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

# Fix for import error: ucimlrepo uses 'fetch' not 'fetch_dataset'
try:
    from ucimlrepo import fetch
except ImportError:
    raise ImportError(
        "ucimlrepo is required. Please install it via requirements.txt:\n"
        "pip install ucimlrepo"
    )

from code.simulation.logging_config import get_logger
from code.simulation.test_runner import run_t_test, run_anova, run_chi_squared
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback
from code.simulation.output_writer import ensure_output_directory

logger = get_logger(__name__)

# Dataset IDs from tasks.md (T029a, T029b, T029c)
DATASET_IDS = {
    "breast_cancer": 197,  # Breast Cancer
    "wine": 198,           # Wine
    "adult": 522           # Adult
}

def ensure_data_raw_dir() -> str:
    """Ensure the data/raw directory exists."""
    path = os.path.join("data", "raw")
    os.makedirs(path, exist_ok=True)
    return path

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_breast_cancer_dataset() -> pd.DataFrame:
    """Download UCI Breast Cancer dataset (ID 197)."""
    logger.info("Downloading Breast Cancer dataset (ID 197)...")
    try:
        data = fetch(code=DATASET_IDS["breast_cancer"], version_tag=None, language='en', download_data=True, download_files=False)
        df = data.data.features
        return df
    except Exception as e:
        logger.error(f"Failed to download Breast Cancer dataset: {e}")
        raise

def download_wine_dataset() -> pd.DataFrame:
    """Download UCI Wine dataset (ID 198)."""
    logger.info("Downloading Wine dataset (ID 198)...")
    try:
        data = fetch(code=DATASET_IDS["wine"], version_tag=None, language='en', download_data=True, download_files=False)
        df = data.data.features
        return df
    except Exception as e:
        logger.error(f"Failed to download Wine dataset: {e}")
        raise

def download_adult_dataset() -> pd.DataFrame:
    """Download UCI Adult dataset (ID 522)."""
    logger.info("Downloading Adult dataset (ID 522)...")
    try:
        data = fetch(code=DATASET_IDS["adult"], version_tag=None, language='en', download_data=True, download_files=False)
        df = data.data.features
        return df
    except Exception as e:
        logger.error(f"Failed to download Adult dataset: {e}")
        raise

def verify_dataset_checksum(df: pd.DataFrame, expected_checksum: Optional[str] = None) -> bool:
    """Verify checksum of a dataset (placeholder logic for real checksums)."""
    # In a real scenario, we would compute checksum of the raw file.
    # Here we just return True if data exists.
    return not df.empty

def register_dataset_in_metadata(dataset_name: str, checksum: str, filepath: str):
    """Register dataset info in metadata file."""
    meta_path = "data/simulation_metadata.json"
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, 'r') as f:
            meta = json.load(f)
    
    if "datasets" not in meta:
        meta["datasets"] = {}
    
    meta["datasets"][dataset_name] = {
        "checksum": checksum,
        "filepath": filepath,
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(meta_path, 'w') as f:
        json.dump(meta, f, indent=2)

def prepare_data_for_ttest(df: pd.DataFrame, target_col: Optional[str] = None, group_col: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare data for t-test.
    If target_col and group_col are provided, split by group.
    Otherwise, assume binary target or split by median.
    """
    if target_col is None:
        # Fallback: use first numeric column
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) == 0:
            raise ValueError("No numeric columns found in dataset")
        target_col = num_cols[0]
    
    if group_col is None:
        # Fallback: split by median
        median_val = df[target_col].median()
        group1 = df[df[target_col] > median_val][target_col].values
        group2 = df[df[target_col] <= median_val][target_col].values
        return group1, group2
    
    if group_col not in df.columns:
        # Try to find a categorical column
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) == 0:
            raise ValueError("No group column found and no categorical columns available")
        group_col = cat_cols[0]
    
    unique_groups = df[group_col].unique()
    if len(unique_groups) < 2:
        raise ValueError(f"Group column '{group_col}' has less than 2 unique values")
    
    # Take first two groups
    g1, g2 = unique_groups[:2]
    group1 = df[df[group_col] == g1][target_col].dropna().values
    group2 = df[df[group_col] == g2][target_col].dropna().values
    
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("One of the groups has insufficient data for t-test")
    
    return group1, group2

def prepare_data_for_anova(df: pd.DataFrame, target_col: Optional[str] = None, group_col: Optional[str] = None) -> List[np.ndarray]:
    """
    Prepare data for ANOVA.
    Returns list of arrays, one per group.
    """
    if target_col is None:
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) == 0:
            raise ValueError("No numeric columns found")
        target_col = num_cols[0]
    
    if group_col is None:
        # Fallback: bin numeric column into 3 groups
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) < 2:
            raise ValueError("Need at least 2 numeric columns to create groups")
        group_col = num_cols[1]
        # Bin into 3 equal frequency groups
        df['_group'] = pd.qcut(df[group_col], q=3, labels=False, duplicates='drop')
        group_col = '_group'
    
    if group_col not in df.columns:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) == 0:
            raise ValueError("No group column and no categorical columns")
        group_col = cat_cols[0]
    
    groups = []
    for _, group_df in df.groupby(group_col):
        vals = group_df[target_col].dropna().values
        if len(vals) >= 2:
            groups.append(vals)
    
    if len(groups) < 2:
        raise ValueError("Not enough groups for ANOVA")
    
    return groups

def prepare_data_for_chi_squared(df: pd.DataFrame, col1: Optional[str] = None, col2: Optional[str] = None) -> np.ndarray:
    """
    Prepare data for Chi-squared test.
    Creates a contingency table from two categorical columns.
    """
    if col1 is None or col2 is None:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) < 2:
            # Try to bin numeric columns if not enough categorical
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) >= 2:
                df['_c1'] = pd.qcut(df[num_cols[0]], q=3, labels=False, duplicates='drop')
                df['_c2'] = pd.qcut(df[num_cols[1]], q=3, labels=False, duplicates='drop')
                col1, col2 = '_c1', '_c2'
            else:
                raise ValueError("Need at least 2 categorical columns for Chi-squared")
        else:
            col1, col2 = cat_cols[0], cat_cols[1]
    
    if col1 not in df.columns or col2 not in df.columns:
        raise ValueError(f"Columns {col1} or {col2} not found in dataset")
    
    contingency = pd.crosstab(df[col1], df[col2])
    return contingency.values

def run_validation_on_datasets(output_path: str = "data/simulation/real_data_pvalues.csv"):
    """
    Run t-test, ANOVA, and chi-squared on real datasets and save p-values.
    """
    ensure_output_directory(output_path)
    
    datasets = {
        "breast_cancer": download_breast_cancer_dataset,
        "wine": download_wine_dataset,
        "adult": download_adult_dataset
    }
    
    results = []
    
    for name, loader in datasets.items():
        logger.info(f"Processing dataset: {name}")
        try:
            df = loader()
            
            # Register checksum (using a hash of the dataframe for now)
            checksum = hashlib.sha256(df.to_json().encode()).hexdigest()
            register_dataset_in_metadata(name, checksum, f"data/raw/{name}.csv")
            
            # Run T-Test
            try:
                g1, g2 = prepare_data_for_ttest(df)
                _, p_ttest = run_t_test(g1, g2)
                results.append({
                    "dataset": name,
                    "test": "t-test",
                    "p_value": p_ttest,
                    "status": "success"
                })
            except Exception as e:
                logger.warning(f"T-test failed on {name}: {e}")
                results.append({
                    "dataset": name,
                    "test": "t-test",
                    "p_value": None,
                    "status": "failed",
                    "error": str(e)
                })
            
            # Run ANOVA
            try:
                groups = prepare_data_for_anova(df)
                _, p_anova = run_anova(groups)
                results.append({
                    "dataset": name,
                    "test": "anova",
                    "p_value": p_anova,
                    "status": "success"
                })
            except Exception as e:
                logger.warning(f"ANOVA failed on {name}: {e}")
                results.append({
                    "dataset": name,
                    "test": "anova",
                    "p_value": None,
                    "status": "failed",
                    "error": str(e)
                })
            
            # Run Chi-squared
            try:
                contingency = prepare_data_for_chi_squared(df)
                _, p_chi = run_chi_squared_with_fallback(contingency)
                results.append({
                    "dataset": name,
                    "test": "chi-squared",
                    "p_value": p_chi,
                    "status": "success"
                })
            except Exception as e:
                logger.warning(f"Chi-squared failed on {name}: {e}")
                results.append({
                    "dataset": name,
                    "test": "chi-squared",
                    "p_value": None,
                    "status": "failed",
                    "error": str(e)
                })
            
        except Exception as e:
            logger.error(f"Failed to process dataset {name}: {e}")
            for test in ["t-test", "anova", "chi-squared"]:
                results.append({
                    "dataset": name,
                    "test": test,
                    "p_value": None,
                    "status": "failed",
                    "error": str(e)
                })
    
    # Save results to CSV
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved real data p-values to {output_path}")
    
    return df_results

def main():
    """Main entry point for validation."""
    output_file = "data/simulation/real_data_pvalues.csv"
    run_validation_on_datasets(output_file)
    logger.info("Validation complete.")

if __name__ == "__main__":
    main()