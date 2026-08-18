"""
Validator module for User Story 3: Validation Against Real-World Small-Sample Datasets.
Downloads real datasets, performs statistical tests, and saves results.
"""
import os
import json
import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from scipy import stats
import warnings

# Import logging utilities from the project's shared logging config
try:
    from code.simulation.logging_config import get_logger, log_operation
except ImportError:
    # Fallback if running from root or different context
    try:
        from simulation.logging_config import get_logger, log_operation
    except ImportError:
        # Minimal fallback if logging module is missing entirely
        def get_logger(name):
            class DummyLogger:
                def info(self, *a, **k): pass
                def debug(self, *a, **k): pass
                def warning(self, *a, **k): pass
                def error(self, *a, **k): pass
            return DummyLogger()
        def log_operation(*a, **k): pass

logger = get_logger(__name__)

# --- Data Download and Checksum Utilities (T029a-d, T029d) ---

def ensure_data_raw_dir() -> str:
    """Ensure data/raw directory exists."""
    path = "data/raw"
    os.makedirs(path, exist_ok=True)
    return path

def compute_file_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_metadata_file_exists() -> str:
    """Ensure simulation_metadata.json exists."""
    path = "data/simulation_metadata.json"
    if not os.path.exists(path):
        base_dir = os.path.dirname(path)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)
        with open(path, 'w') as f:
            json.dump({"seeds": {}, "config": {}, "timestamps": {}, "datasets": {}}, f)
    return path

def load_simulation_metadata() -> Dict[str, Any]:
    """Load simulation metadata."""
    path = ensure_metadata_file_exists()
    with open(path, 'r') as f:
        return json.load(f)

def save_simulation_metadata(data: Dict[str, Any]) -> None:
    """Save simulation metadata."""
    path = ensure_metadata_file_exists()
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def download_breast_cancer_dataset() -> str:
    """Download UCI Breast Cancer (Wisconsin Diagnostic) dataset (ID 197)."""
    try:
        from ucimlrepo import fetch_ucirepo
        logger.info("Fetching UCI Breast Cancer dataset (ID 197)...")
        bc_dataset = fetch_ucirepo(id=197)
        df = bc_dataset.data.features
        # Save to CSV
        output_path = "data/raw/breast_cancer_wisconsin.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Downloaded and saved to {output_path}")
        return output_path
    except ImportError:
        raise RuntimeError("ucimlrepo package is required to download UCI datasets. Install it via pip.")
    except Exception as e:
        logger.error(f"Failed to download Breast Cancer dataset: {e}")
        raise

def download_wine_dataset() -> str:
    """Download UCI Wine dataset (ID 198)."""
    try:
        from ucimlrepo import fetch_ucirepo
        logger.info("Fetching UCI Wine dataset (ID 198)...")
        wine_dataset = fetch_ucirepo(id=198)
        df = wine_dataset.data.features
        output_path = "data/raw/wine.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Downloaded and saved to {output_path}")
        return output_path
    except ImportError:
        raise RuntimeError("ucimlrepo package is required to download UCI datasets. Install it via pip.")
    except Exception as e:
        logger.error(f"Failed to download Wine dataset: {e}")
        raise

def download_adult_dataset() -> str:
    """Download OpenML Adult dataset (ID 522) via ucimlrepo."""
    try:
        from ucimlrepo import fetch_ucirepo
        logger.info("Fetching OpenML Adult dataset (ID 522)...")
        adult_dataset = fetch_ucirepo(id=522)
        df = adult_dataset.data.features
        output_path = "data/raw/adult.csv"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Downloaded and saved to {output_path}")
        return output_path
    except ImportError:
        raise RuntimeError("ucimlrepo package is required to download UCI datasets. Install it via pip.")
    except Exception as e:
        logger.error(f"Failed to download Adult dataset: {e}")
        raise

def verify_dataset_checksum(filepath: str, expected_checksum: Optional[str] = None) -> bool:
    """Verify dataset checksum against recorded value or return computed value."""
    computed = compute_file_checksum(filepath)
    if expected_checksum:
        return computed == expected_checksum
    return True

def register_dataset_in_metadata(dataset_name: str, filepath: str, checksum: str) -> None:
    """Register dataset checksum in metadata."""
    metadata = load_simulation_metadata()
    if "datasets" not in metadata:
        metadata["datasets"] = {}
    metadata["datasets"][dataset_name] = {
        "path": filepath,
        "checksum": checksum,
        "downloaded_at": str(pd.Timestamp.utcnow())
    }
    save_simulation_metadata(metadata)

# --- Data Preprocessing (T030) ---

def prepare_data_for_ttest(filepath: str, target_col: str, group_col: Optional[str] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare data for t-test. If group_col is provided, split by it."""
    df = pd.read_csv(filepath)
    if group_col:
        groups = df[group_col].unique()
        if len(groups) < 2:
            raise ValueError(f"Need at least 2 groups in '{group_col}' for t-test.")
        # Take first two groups
        g1 = df[df[group_col] == groups[0]][target_col].dropna().values
        g2 = df[df[group_col] == groups[1]][target_col].dropna().values
        if len(g1) < 2 or len(g2) < 2:
            raise ValueError("Need at least 2 samples per group for t-test.")
        return g1, g2
    else:
        # Default: compare against a mean of 0 or split into two halves if no group
        # For validation, we'll assume a specific column is the target and split by a binary column if available
        # If not, we'll just return the column and a dummy group for testing purposes (though not ideal)
        # Better: assume the first numeric column is target, and a binary column exists
        raise NotImplementedError("Group column required for t-test preparation in this context.")

def prepare_data_for_anova(filepath: str, target_col: str, group_col: str) -> List[np.ndarray]:
    """Prepare data for ANOVA. Split by group_col."""
    df = pd.read_csv(filepath)
    groups = df[group_col].unique()
    data_groups = []
    for g in groups:
        vals = df[df[group_col] == g][target_col].dropna().values
        if len(vals) > 0:
            data_groups.append(vals)
    if len(data_groups) < 2:
        raise ValueError("Need at least 2 groups for ANOVA.")
    return data_groups

def prepare_data_for_chi_squared(filepath: str, col1: str, col2: str) -> np.ndarray:
    """Prepare data for chi-squared test. Create contingency table."""
    df = pd.read_csv(filepath)
    # Create contingency table
    table = pd.crosstab(df[col1], df[col2])
    return table.values

# --- Statistical Tests Implementation (T031) ---

def run_t_test(group1: np.ndarray, group2: np.ndarray) -> Dict[str, Any]:
    """Run independent t-test and return p-value."""
    try:
        stat, p_value = stats.ttest_ind(group1, group2)
        return {"statistic": float(stat), "p_value": float(p_value), "method": "t-test"}
    except Exception as e:
        logger.error(f"t-test failed: {e}")
        return {"statistic": None, "p_value": None, "method": "t-test", "error": str(e)}

def run_anova(groups: List[np.ndarray]) -> Dict[str, Any]:
    """Run one-way ANOVA and return p-value."""
    try:
        stat, p_value = stats.f_oneway(*groups)
        return {"statistic": float(stat), "p_value": float(p_value), "method": "anova"}
    except Exception as e:
        logger.error(f"ANOVA failed: {e}")
        return {"statistic": None, "p_value": None, "method": "anova", "error": str(e)}

def run_chi_squared(table: np.ndarray) -> Dict[str, Any]:
    """Run chi-squared test and return p-value."""
    try:
        # Handle 2x2 with Yates correction if needed, or general chi2
        if table.shape == (2, 2):
            stat, p_value, dof, expected = stats.chi2_contingency(table, correction=True)
            method = "chi2_yates"
        else:
            stat, p_value, dof, expected = stats.chi2_contingency(table, correction=False)
            method = "chi2"
        return {"statistic": float(stat), "p_value": float(p_value), "method": method}
    except Exception as e:
        logger.error(f"Chi-squared test failed: {e}")
        return {"statistic": None, "p_value": None, "method": "chi2", "error": str(e)}

# --- Main Validation Logic (T031) ---

def run_validation_on_datasets() -> List[Dict[str, Any]]:
    """
    Run t-test, ANOVA, and chi-squared on real datasets.
    Returns a list of results with dataset_id, test_type, and p_value.
    """
    results = []

    # Define datasets and test configurations
    # Note: We need to select appropriate columns for each test from the real data
    datasets = [
        {
            "id": "breast_cancer",
            "path": download_breast_cancer_dataset(),
            "tests": [
                # T-test: Compare mean of 'mean radius' between diagnosis classes (M vs B)
                {"type": "t-test", "target": "mean radius", "group": "diagnosis"},
                # ANOVA: Not directly applicable unless we bin a continuous variable, skipping for simplicity or using 3+ groups if available
                # Chi-squared: Not directly applicable on continuous features without binning
            ]
        },
        {
            "id": "wine",
            "path": download_wine_dataset(),
            "tests": [
                # T-test: Compare 'alcohol' between two classes (0 and 1)
                {"type": "t-test", "target": "alcohol", "group": "class"},
                # ANOVA: Compare 'alcohol' across all 3 classes
                {"type": "anova", "target": "alcohol", "group": "class"},
                # Chi-squared: Not directly applicable without binning
            ]
        },
        {
            "id": "adult",
            "path": download_adult_dataset(),
            "tests": [
                # Chi-squared: Relationship between 'education' and 'income'
                {"type": "chi-squared", "col1": "education", "col2": "class"}, # class is the target in adult dataset usually 'class' or 'income'
                # T-test: Compare 'age' between income classes
                {"type": "t-test", "target": "age", "group": "class"}
            ]
        }
    ]

    for ds in datasets:
        ds_path = ds["path"]
        ds_id = ds["id"]
        logger.info(f"Processing dataset: {ds_id}")

        # Load data once per dataset
        df = pd.read_csv(ds_path)
        logger.debug(f"Dataset {ds_id} shape: {df.shape}")

        for test_config in ds["tests"]:
            test_type = test_config["type"]
            p_value = None

            try:
                if test_type == "t-test":
                    target = test_config["target"]
                    group = test_config["group"]
                    if target not in df.columns or group not in df.columns:
                        logger.warning(f"Columns {target} or {group} not found in {ds_id}. Skipping.")
                        continue
                    g1, g2 = prepare_data_for_ttest(ds_path, target, group)
                    res = run_t_test(g1, g2)
                    p_value = res["p_value"]
                    logger.info(f"{ds_id} t-test p-value: {p_value}")

                elif test_type == "anova":
                    target = test_config["target"]
                    group = test_config["group"]
                    if target not in df.columns or group not in df.columns:
                        logger.warning(f"Columns {target} or {group} not found in {ds_id}. Skipping.")
                        continue
                    groups_data = prepare_data_for_anova(ds_path, target, group)
                    res = run_anova(groups_data)
                    p_value = res["p_value"]
                    logger.info(f"{ds_id} ANOVA p-value: {p_value}")

                elif test_type == "chi-squared":
                    col1 = test_config["col1"]
                    col2 = test_config["col2"]
                    if col1 not in df.columns or col2 not in df.columns:
                        logger.warning(f"Columns {col1} or {col2} not found in {ds_id}. Skipping.")
                        continue
                    table = prepare_data_for_chi_squared(ds_path, col1, col2)
                    res = run_chi_squared(table)
                    p_value = res["p_value"]
                    logger.info(f"{ds_id} Chi-squared p-value: {p_value}")

                if p_value is not None:
                    results.append({
                        "dataset_id": ds_id,
                        "test_type": test_type,
                        "p_value": p_value
                    })
                else:
                    # Log if p_value is None but no error occurred (e.g., insufficient data)
                    logger.warning(f"P-value is None for {ds_id} {test_type}.")

            except Exception as e:
                logger.error(f"Error running {test_type} on {ds_id}: {e}")
                results.append({
                    "dataset_id": ds_id,
                    "test_type": test_type,
                    "p_value": None,
                    "error": str(e)
                })

    return results

def save_p_values_to_csv(results: List[Dict[str, Any]], output_path: str = "data/simulation/real_data_pvalues.csv") -> None:
    """Save p-value results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved real data p-values to {output_path}")

def load_p_values_to_csv_safe(filepath: str = "data/simulation/real_data_pvalues.csv") -> pd.DataFrame:
    """Load p-value results from CSV safely."""
    if not os.path.exists(filepath):
        return pd.DataFrame(columns=["dataset_id", "test_type", "p_value"])
    return pd.read_csv(filepath)

def main():
    """Main entry point for T031."""
    logger.info("Starting T031: Run statistical tests on real datasets.")
    results = run_validation_on_datasets()
    save_p_values_to_csv(results)
    logger.info("T031 completed.")

if __name__ == "__main__":
    main()