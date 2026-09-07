import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import from utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging_utils import init_exclusion_log, log_exclusion, log_warning, log_disclaimer
from utils.validators import validate_variable_presence, get_required_columns
from utils.dataset_loaders import load_adult, load_compas, load_bank, load_german, load_lawschool

# Import data model
from data_model import Dataset

def log_header(header_text: str) -> None:
    """Print a formatted header to console."""
    print("\n" + "=" * 60)
    print(f" {header_text}")
    print("=" * 60)
    log_disclaimer()

def get_file_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_and_validate_dataset(dataset_id: str) -> Optional[Dataset]:
    """
    Load a dataset by ID and validate required variables.
    Returns Dataset object or None if validation fails.
    """
    loaders = {
        "adult": load_adult,
        "compas": load_compas,
        "bank": load_bank,
        "german": load_german,
        "lawschool": load_lawschool
    }

    if dataset_id not in loaders:
        log_warning(f"Unknown dataset ID: {dataset_id}")
        return None

    try:
        df = loaders[dataset_id]()
        if df is None:
            log_warning(f"Failed to load dataset: {dataset_id}")
            return None
    except Exception as e:
        log_warning(f"Error loading {dataset_id}: {str(e)}")
        return None

    # Define required columns (example: protected, outcome, prediction)
    # In a real scenario, these would be defined per dataset or in a config
    required_cols = get_required_columns(dataset_id)
    
    if not validate_variable_presence(df, required_cols):
        log_exclusion(dataset_id, "missing_variables", f"Missing required columns: {required_cols}")
        return None

    return Dataset(dataset_id=dataset_id, data=df)

def binarize_column(df: Any, column_name: str, mapping: Optional[Dict] = None) -> Any:
    """
    Binarize a column. If mapping is provided, use it; otherwise, assume 0/1 or True/False.
    """
    if mapping:
        df[column_name] = df[column_name].map(mapping)
    else:
        # Simple binary conversion if not already 0/1
        if df[column_name].dtype == 'object':
            unique_vals = df[column_name].unique()
            if len(unique_vals) == 2:
                df[column_name] = df[column_name].map({unique_vals[0]: 0, unique_vals[1]: 1})
    return df

def map_categorical_to_binary(df: Any, column_name: str, positive_class: Any) -> Any:
    """
    Map a categorical column to binary where positive_class becomes 1, others 0.
    """
    df[column_name] = df[column_name].apply(lambda x: 1 if x == positive_class else 0)
    return df

def stratified_sample(df: Any, target_col: str, max_rows: int = 100000, random_state: int = 42) -> Any:
    """
    Perform stratified sampling to ensure at most max_rows while preserving class distribution.
    """
    if len(df) <= max_rows:
        return df
    
    # Ensure random_state is used for reproducibility
    return df.groupby(target_col, group_keys=False).apply(
        lambda x: x.sample(n=min(int(len(x) * (max_rows / len(df))), len(x)), random_state=random_state)
    )

def preprocess_dataset(dataset: Dataset) -> Dataset:
    """
    Preprocess a dataset:
    - Binarize protected attributes and outcomes if necessary
    - Perform stratified sampling to <= 100k rows
    - Log disclaimers
    """
    log_header(f"Preprocessing Dataset: {dataset.dataset_id}")
    log_disclaimer()

    df = dataset.data.copy()

    # Example: Assume column 'sex' or 'gender' is protected, 'income' or 'class' is outcome
    # This logic should be more robust in a real implementation
    protected_cols = [col for col in df.columns if 'sex' in col.lower() or 'gender' in col.lower() or 'race' in col.lower()]
    outcome_cols = [col for col in df.columns if 'income' in col.lower() or 'class' in col.lower() or 'default' in col.lower()]

    for col in protected_cols:
        if df[col].dtype != 'int64' and df[col].dtype != 'float64':
            df = binarize_column(df, col)

    for col in outcome_cols:
        if df[col].dtype != 'int64' and df[col].dtype != 'float64':
            df = binarize_column(df, col)

    # Stratified sample
    target = outcome_cols[0] if outcome_cols else protected_cols[0]
    if target and target in df.columns:
        df = stratified_sample(df, target, max_rows=100000, random_state=42)

    dataset.data = df
    return dataset

def save_processed_dataset(dataset: Dataset, output_path: str) -> str:
    """
    Save processed dataset to CSV and return its checksum.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    dataset.data.to_csv(output_path, index=False)
    checksum = get_file_checksum(output_path)
    return checksum

def preprocess_dataset_workflow() -> None:
    """
    Main workflow for preprocessing all datasets.
    """
    log_header("Preprocessing Workflow")
    
    dataset_ids = ["adult", "compas", "bank", "german", "lawschool"]
    processed_datasets = []

    for ds_id in dataset_ids:
        dataset = load_and_validate_dataset(ds_id)
        if dataset is None:
            continue
        
        processed_dataset = preprocess_dataset(dataset)
        output_path = f"data/processed/{ds_id}_processed.csv"
        checksum = save_processed_dataset(processed_dataset, output_path)
        processed_datasets.append({
            "dataset_id": ds_id,
            "path": output_path,
            "checksum": checksum
        })
        log_warning(f"Processed {ds_id} saved to {output_path} with checksum {checksum}")

    # Log completion
    log_header("Preprocessing Complete")
    log_disclaimer()

def main():
    preprocess_dataset_workflow()

if __name__ == "__main__":
    main()
