"""
GateMem Dataset Loader and Validator.

This module handles fetching the GateMem dataset from HuggingFace
and validating its schema for downstream processing.
"""

import os
import json
from typing import Dict, List, Any, Optional
import pandas as pd
from datasets import load_dataset

# Project root relative to this file
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw')
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'data', 'logs')

# Ensure directories exist
os.makedirs(DATA_RAW_DIR, exist_ok=True)
os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# GateMem dataset configuration
# Using the verified HuggingFace dataset path
GATEMEM_DATASET_NAME = "gatekeeper-ai/gatemem"
GATEMEM_CONFIG = "default"


def fetch_gatemem() -> pd.DataFrame:
    """
    Download and load the GateMem dataset from HuggingFace.

    Returns:
        pd.DataFrame: The loaded dataset as a pandas DataFrame.

    Raises:
        RuntimeError: If the dataset cannot be fetched or loaded.
    """
    cache_dir = os.path.join(DATA_RAW_DIR, "huggingface_cache")
    os.makedirs(cache_dir, exist_ok=True)

    try:
        dataset = load_dataset(
            GATEMEM_DATASET_NAME,
            GATEMEM_CONFIG,
            cache_dir=cache_dir
        )

        # Assuming the dataset has a 'train' or 'test' split, or a single split
        # We take the first available split for this task
        if "train" in dataset:
            df = dataset["train"].to_pandas()
        elif "test" in dataset:
            df = dataset["test"].to_pandas()
        else:
            split_name = list(dataset.keys())[0]
            df = dataset[split_name].to_pandas()

        # Save raw copy for reference
        raw_path = os.path.join(DATA_RAW_DIR, "gatemem_raw.parquet")
        df.to_parquet(raw_path, index=False)

        return df

    except Exception as e:
        raise RuntimeError(f"Failed to fetch GateMem dataset: {e}")


def validate_fields(df: pd.DataFrame, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate that the dataset contains required fields: 'leak-target' and 'role'.

    Args:
        df: The pandas DataFrame to validate.
        output_path: Optional path to write the validation report JSON.
                     Defaults to data/processed/validation_report.json.

    Returns:
        Dict containing validation results:
            - 'valid': bool (True if all required fields exist)
            - 'missing_fields': List[str] (fields that are missing)
            - 'field_counts': Dict[str, int] (count of non-null values per field)
            - 'sample_values': Dict[str, Any] (first non-null value for each field)

    Raises:
        ValueError: If required fields are missing.
    """
    required_fields = ["leak-target", "role"]
    missing_fields = []
    field_counts = {}
    sample_values = {}

    for field in required_fields:
        if field not in df.columns:
            missing_fields.append(field)
            field_counts[field] = 0
            sample_values[field] = None
        else:
            count = df[field].notna().sum()
            field_counts[field] = int(count)
            # Get first non-null value
            non_null = df[field].dropna()
            if len(non_null) > 0:
                sample_values[field] = str(non_null.iloc[0])
            else:
                sample_values[field] = None

    is_valid = len(missing_fields) == 0

    result = {
        "valid": is_valid,
        "missing_fields": missing_fields,
        "field_counts": field_counts,
        "sample_values": sample_values,
        "total_rows": int(len(df))
    }

    # Write report to disk if output_path is provided or default
    report_path = output_path or os.path.join(DATA_PROCESSED_DIR, "validation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    if not is_valid:
        raise ValueError(f"Dataset validation failed. Missing required fields: {missing_fields}")

    return result


def inject_fallback_data(df: pd.DataFrame, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Implement fallback strategy for missing 'leak-target' fields.

    If 'leak-target' is missing or null in a row, this function attempts to
    derive a ground-truth label from the existing 'rule-log' field.
    - If 'rule-log' indicates a violation (e.g., contains "DENIED", "BLOCK", or specific
      rejection codes), the fallback assigns 'leak-target' = 1 (leak/violation).
    - If 'rule-log' indicates success or is empty/neutral, the fallback assigns 'leak-target' = 0.
    - If 'rule-log' is also missing, the row is marked as 'unrecoverable' and skipped.

    NO synthetic data is generated; this strictly repurposes existing logged rule outcomes.

    Args:
        df: The pandas DataFrame to process.
        output_path: Optional path to write the processed dataset.
                     Defaults to data/processed/gatemem_fallback.parquet.

    Returns:
        Dict containing fallback statistics:
            - 'total_rows': int
            - 'missing_leak_target': int
            - 'fallback_applied': int
            - 'fallback_unrecoverable': int
            - 'output_path': str
    """
    total_rows = len(df)
    missing_leak_target = 0
    fallback_applied = 0
    fallback_unrecoverable = 0

    # Ensure 'leak-target' column exists, fill NaNs temporarily
    if "leak-target" not in df.columns:
        df["leak-target"] = float('nan')

    # Identify rows where 'leak-target' is missing/NaN
    missing_mask = df["leak-target"].isna()
    missing_leak_target = int(missing_mask.sum())

    if missing_leak_target == 0:
        # No fallback needed
        return {
            "total_rows": total_rows,
            "missing_leak_target": 0,
            "fallback_applied": 0,
            "fallback_unrecoverable": 0,
            "output_path": output_path or os.path.join(DATA_PROCESSED_DIR, "gatemem_fallback.parquet"),
            "message": "No missing leak-target values found."
        }

    # Define heuristic for rule-log interpretation
    # Common indicators of a blocked/leaked request in logs
    denial_keywords = ["DENIED", "BLOCK", "REJECTED", "VIOLATION", "FAIL", "UNAUTHORIZED"]

    def resolve_leak_target(row):
        nonlocal fallback_applied, fallback_unrecoverable
        
        current_target = row["leak-target"]
        if pd.notna(current_target):
            return current_target

        rule_log = row.get("rule-log")
        
        if pd.isna(rule_log) or (isinstance(rule_log, str) and rule_log.strip() == ""):
            fallback_unrecoverable += 1
            return float('nan') # Keep as NaN if no info

        rule_log_str = str(rule_log).upper()
        
        # Check for denial keywords
        has_denial = any(kw in rule_log_str for kw in denial_keywords)
        
        if has_denial:
            fallback_applied += 1
            return 1 # Leak/Violation detected via rule log
        else:
            fallback_applied += 1
            return 0 # No leak detected via rule log

    # Apply fallback logic
    df["leak-target"] = df.apply(resolve_leak_target, axis=1)

    # Prepare output path
    out_path = output_path or os.path.join(DATA_PROCESSED_DIR, "gatemem_fallback.parquet")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Save processed dataset
    df.to_parquet(out_path, index=False)

    stats = {
        "total_rows": total_rows,
        "missing_leak_target": missing_leak_target,
        "fallback_applied": fallback_applied,
        "fallback_unrecoverable": fallback_unrecoverable,
        "output_path": out_path
    }

    # Log summary
    log_path = os.path.join(LOGS_DIR, "fallback_strategy.log")
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"Fallback Strategy Execution Log\n")
        f.write(f"Total Rows: {total_rows}\n")
        f.write(f"Missing leak-target: {missing_leak_target}\n")
        f.write(f"Fallback applied: {fallback_applied}\n")
        f.write(f"Unrecoverable (no rule-log): {fallback_unrecoverable}\n")
        f.write(f"Output saved to: {out_path}\n")

    return stats


def run_validation_pipeline():
    """
    Main entry point to fetch, validate, and apply fallback strategy to the GateMem dataset.
    Writes validation report to data/processed/validation_report.json and processed data to data/processed/gatemem_fallback.parquet.
    """
    print("Fetching GateMem dataset...")
    df = fetch_gatemem()
    print(f"Dataset loaded: {len(df)} rows, columns: {list(df.columns)}")

    print("Validating fields...")
    try:
        report = validate_fields(df)
        print("Validation successful!")
        print(json.dumps(report, indent=2))
    except ValueError as e:
        print(f"Validation failed: {e}")
        # We continue to fallback even if validation fails on missing fields
        # because the fallback is designed to handle this case.
    
    print("\nApplying fallback strategy for missing leak-target...")
    try:
        fallback_stats = inject_fallback_data(df)
        print("Fallback strategy applied successfully!")
        print(json.dumps(fallback_stats, indent=2))
    except Exception as e:
        print(f"Fallback strategy failed: {e}")
        raise

    return report, fallback_stats


if __name__ == "__main__":
    run_validation_pipeline()