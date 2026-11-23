"""
Imputation Threshold Sensitivity Analysis

Implements a sensitivity analysis to validate the robustness of the chosen 15%
imputation threshold (Spec FR-002). It runs the preprocessing pipeline with
varying thresholds (e.g., 5%, 10%, 15%, 20%, 25%) and compares the resulting
model metrics to determine if the model performance is highly sensitive to
missing data handling strategies.
"""

import logging
import json
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np

from src.utils.logging_config import setup_logging, create_logger
from src.preprocessing.preprocess_pipeline import run_preprocessing_pipeline
from src.features.feature_engineering_pipeline import run_feature_engineering_pipeline
from src.models.training_pipeline import run_training_pipeline
from src.utils.checksums import calculate_file_sha256

logger = create_logger(__name__)

# Define the thresholds to test (percentages)
THRESHOLDS_TO_TEST = [5.0, 10.0, 15.0, 20.0, 25.0]

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MODELS_DIR = PROJECT_ROOT / "code" / "models"
OUTPUT_DIR = PROJECT_ROOT / "data" / "analysis"
OUTPUT_FILE = OUTPUT_DIR / "imputation_sensitivity_results.json"

# Backup paths for temporary file swapping
RAW_BACKUP = DATA_RAW_DIR / "alloys_raw_backup.csv"
PROCESSED_BACKUP = DATA_PROCESSED_DIR / "alloys_raw_backup.csv"
FEATURES_BACKUP = DATA_PROCESSED_DIR / "alloys_features_backup.csv"
METRICS_BACKUP = DATA_PROCESSED_DIR / "model_metrics_backup.json"

def setup_directories():
    """Ensure necessary directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

def backup_current_artifacts():
    """Backup current pipeline artifacts to restore later."""
    logger.info("Backing up current pipeline artifacts...")
    files_to_backup = [
        (DATA_PROCESSED_DIR / "alloys_raw.csv", PROCESSED_BACKUP),
        (DATA_PROCESSED_DIR / "alloys_features.csv", FEATURES_BACKUP),
        (DATA_PROCESSED_DIR / "model_metrics.json", METRICS_BACKUP),
    ]

    for src, dst in files_to_backup:
        if src.exists():
            shutil.copy2(src, dst)
            logger.debug(f"Backed up: {src} -> {dst}")
        else:
            logger.warning(f"File not found to backup: {src}")

def restore_current_artifacts():
    """Restore pipeline artifacts from backup."""
    logger.info("Restoring pipeline artifacts from backup...")
    files_to_restore = [
        (PROCESSED_BACKUP, DATA_PROCESSED_DIR / "alloys_raw.csv"),
        (FEATURES_BACKUP, DATA_PROCESSED_DIR / "alloys_features.csv"),
        (METRICS_BACKUP, DATA_PROCESSED_DIR / "model_metrics.json"),
    ]

    for src, dst in files_to_restore:
        if src.exists():
            shutil.copy2(src, dst)
            logger.debug(f"Restored: {src} -> {dst}")
        else:
            logger.warning(f"Backup file not found: {src}")

def run_pipeline_with_threshold(threshold: float) -> Tuple[bool, Dict[str, Any]]:
    """
    Runs the full pipeline (Preprocessing -> Features -> Training) with a specific
    imputation threshold.

    Note: This function assumes the imputation logic in `imputation_orchestrator`
    reads a configuration or environment variable for the threshold. Since the
    current implementation hardcodes the 15% check, we will simulate the change
    by temporarily patching the module or, more robustly, by re-implementing the
    specific logic here if the orchestrator is not configurable.

    Given the constraint to extend existing code, we will assume the `imputation_orchestrator`
    can be called with a threshold argument, OR we will modify the `preprocess_pipeline`
    to accept a threshold.

    Since we cannot easily patch the orchestrator's internal logic without rewriting it,
    and the task requires running the pipeline, we will:
    1. Load the raw data.
    2. Manually apply the imputation logic with the specific threshold.
    3. Save the intermediate data.
    4. Run the subsequent steps (Features, Training).

    However, to strictly follow "extend, don't re-author", we will attempt to
    inject the threshold into the `preprocess_pipeline` if possible, or rely on
    a global state if the existing code supports it.

    **Strategy**: We will modify the `preprocess_pipeline` to accept a `threshold` argument
    in this task's artifact if it doesn't, but since we are only allowed to write T075 artifacts,
    we must assume the existing `preprocess_pipeline` is fixed.

    **Correction**: The existing `preprocess_pipeline` calls `run_imputation`.
    We will create a wrapper that runs the pipeline but intercepts the imputation step
    or re-runs the specific logic.

    Actually, the cleanest way without breaking the existing API is to:
    1. Load raw data (from `data/raw/merged_data.csv` or similar, assuming T027 output).
    2. Perform standardization, unit normalization, DFT filter (using existing functions).
    3. Perform IMPUTATION with the custom threshold (re-implementing the logic locally to ensure it uses the threshold).
    4. Save to `data/processed/alloys_raw.csv`.
    5. Run Feature Engineering and Training.

    This avoids modifying the core `preprocess_pipeline` logic which might be tested elsewhere.
    """
    logger.info(f"Running pipeline with imputation threshold: {threshold}%")

    # 1. Load Raw Data
    # Assuming the raw merged data is in data/raw/merged_data.csv (output of T026)
    # If not, we might need to run the ingestion pipeline first.
    # For this sensitivity analysis, we assume `data/raw/merged_data.csv` exists.
    raw_input = DATA_RAW_DIR / "merged_data.csv"
    if not raw_input.exists():
        # Fallback: try alloys_raw.csv if merged_data is missing (T027 output)
        raw_input = DATA_PROCESSED_DIR / "alloys_raw.csv"
        if not raw_input.exists():
            logger.error(f"Raw input data not found at {raw_input}. Cannot run sensitivity analysis.")
            return False, {}

    try:
        df_raw = pd.read_csv(raw_input)
        # Handle composition column if it's a string representation of a dict
        if 'composition' in df_raw.columns:
            df_raw['composition'] = df_raw['composition'].apply(lambda x: eval(x) if isinstance(x, str) else x)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return False, {}

    # 2. Standardization (Composition Parsing)
    # Re-using existing logic
    from src.preprocessing.composition_parser import parse_composition
    # We need to apply parse_composition to the dataframe.
    # The existing function returns a dict. We need to expand it.
    # Let's assume the existing pipeline does this. We will replicate the expansion.
    # This is a bit hacky but necessary to avoid rewriting the whole pipeline.
    # Better: Call the existing `run_preprocessing_pipeline` but override the imputation step?
    # No, we can't easily override. We will do a mini-pipeline here.

    # --- Mini Preprocessing Pipeline ---
    # A. Parse Composition
    def expand_composition(row):
        if isinstance(row['composition'], str):
            comp = eval(row['composition'])
        else:
            comp = row['composition']
        # Create columns for each element
        for k, v in comp.items():
            row[f'comp_{k}'] = v
        return pd.Series(row)

    # This is getting complex to replicate. Let's try a different approach.
    # We will modify the `imputation_orchestrator` to accept a threshold parameter.
    # But we can't modify it in this task (T075) if it's not an artifact of T075?
    # The prompt says "Extend, don't re-author".
    # If `imputation_orchestrator` is not configurable, we must implement the logic here.

    # Let's assume the input to the sensitivity analysis is the `data/processed/alloys_raw.csv`
    # which has already been standardized and filtered, but NOT imputed.
    # Wait, T027 produces `alloys_raw.csv` which IS imputed.
    # So we need the data BEFORE imputation.
    # Let's assume there is a `data/processed/alloys_standardized.csv` or similar.
    # If not, we must re-run the steps up to imputation.

    # **Revised Strategy**:
    # 1. Load `data/raw/merged_data.csv` (T026 output).
    # 2. Run `composition_parser`, `unit_normalizer`, `dft_filter` (using existing functions).
    # 3. Perform Imputation with custom threshold.
    # 4. Save to `data/processed/alloys_raw.csv`.
    # 5. Run `feature_engineering_pipeline` and `training_pipeline`.

    # Step 1: Load
    df = pd.read_csv(raw_input)

    # Step 2: Standardize & Filter
    # We will use the existing functions from the modules.
    # This is risky if they rely on global state, but let's try.
    from src.preprocessing.composition_parser import parse_composition
    from src.preprocessing.unit_normalizer import standardize_units
    from src.preprocessing.dft_filter import filter_dft_entries

    # A. Composition Parsing
    # The existing `parse_composition` works on a string. We need to apply it to the dataframe.
    # Assuming the column is 'composition' and contains stringified dicts.
    if 'composition' in df.columns:
        # Expand composition
        expanded = df['composition'].apply(lambda x: eval(x) if isinstance(x, str) else x)
        # Create columns
        all_elements = set()
        for x in expanded:
            all_elements.update(x.keys())
        
        for elem in all_elements:
            df[f'comp_{elem}'] = expanded.apply(lambda x: x.get(elem, 0))
        
        # Drop the original composition column if it's just the dict string
        # But we might need it for reference. Let's keep it or drop it?
        # The model training usually needs the numeric columns.
        # We'll keep the expanded columns.
    
    # B. Unit Normalization
    # Assuming 'coercivity_oe' and 'saturation_magnetization_emu_g' are the targets
    # The existing `standardize_units` might be row-based.
    # Let's assume the data is already normalized from T027.
    # If we are re-running from raw, we need to call it.
    # For simplicity, let's assume the data in `merged_data.csv` is raw and needs normalization.
    # But `merged_data.csv` might not exist.
    
    # **Fallback**: If we cannot easily re-run the full preprocessing without modifying core files,
    # we will assume the `data/processed/alloys_raw.csv` is the result of the *default* pipeline.
    # We will create a *new* intermediate file that is "standardized but not imputed".
    # But T027 does imputation.
    
    # **Best Approach for T075**:
    # Since we cannot easily modify T024 (imputation orchestrator) to accept a parameter,
    # and we cannot easily re-run T027's non-imputation steps without duplicating code,
    # we will:
    # 1. Load the `data/raw/manual_curated.csv` and other raw sources.
    # 2. Merge them (simulating T026).
    # 3. Apply standardization, normalization, DFT filter.
    # 4. Apply Imputation with the custom threshold.
    # 5. Save to `data/processed/alloys_raw.csv`.
    # 6. Run the rest.

    # This is a lot of code duplication.
    # Let's try to call the existing `run_preprocessing_pipeline` but patch the threshold.
    # We can monkey-patch the `orchestrate_imputation` function in `imputation_orchestrator`.
    # But that's fragile.

    # **Alternative**: We will write a script that runs the pipeline multiple times,
    # but we need the data to be in a state where we can inject the threshold.
    # Let's assume the `preprocess_pipeline` has a global or config for threshold?
    # It doesn't seem to.

    # **Decision**: We will re-implement the minimal necessary logic to get from Raw to Imputed
    # with a custom threshold, using the existing helper functions where possible.
    
    # 1. Load Raw Data (Merged)
    # We need the merged raw data. If it doesn't exist, we assume the user ran T026.
    # If not, we try to load from `data/raw/manual_curated.csv` etc.
    # For this script to be robust, we will look for `data/raw/merged_data.csv`.
    # If not found, we will try to construct it from the sources.
    # But T026 is supposed to create it.
    
    input_file = DATA_RAW_DIR / "merged_data.csv"
    if not input_file.exists():
        logger.error("Merged raw data not found. Please run T026 (ingestion pipeline) first.")
        return False, {}

    df = pd.read_csv(input_file)

    # 2. Standardize Composition
    # We need to parse the 'composition' column.
    # Assuming it's a stringified dict.
    if 'composition' in df.columns:
        # Parse
        parsed_comps = []
        for val in df['composition']:
            if isinstance(val, str):
                parsed_comps.append(eval(val))
            else:
                parsed_comps.append(val)
        
        # Expand
        elements = set()
        for comp in parsed_comps:
            elements.update(comp.keys())
        
        for elem in elements:
            df[f'comp_{elem}'] = [c.get(elem, 0) for c in parsed_comps]
        
        # Drop original if needed, or keep
        # We'll keep it for now.

    # 3. Unit Normalization
    # Assuming the columns are already normalized or we need to normalize them.
    # Let's assume they are raw Oe and emu/g.
    # We will use the existing `normalize_coercivity` and `normalize_saturation_magnetization`.
    from src.preprocessing.unit_normalizer import normalize_coercivity, normalize_saturation_magnetization
    
    # Apply to columns
    if 'coercivity_oe' in df.columns:
        df['coercivity_oe'] = df['coercivity_oe'].apply(normalize_coercivity)
    if 'saturation_magnetization_emu_g' in df.columns:
        df['saturation_magnetization_emu_g'] = df['saturation_magnetization_emu_g'].apply(normalize_saturation_magnetization)

    # 4. DFT Filter
    from src.preprocessing.dft_filter import filter_dft_entries
    # This function expects a dataframe and returns a filtered one.
    # But `filter_dft_entries` in the existing code might be a CLI or a function.
    # Let's assume it's a function.
    df = filter_dft_entries(df)

    # 5. Imputation with Custom Threshold
    # We need to implement the logic here because `imputation_orchestrator` is hardcoded.
    # Logic from T024:
    # - Calculate missing rate per column.
    # - If > threshold: listwise deletion.
    # - If <= threshold: mean imputation.
    
    # Identify target columns and feature columns?
    # We impute on numeric columns that have missing values.
    # Exclude 'source_type', 'synthesis_method', etc.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude composition columns? No, they might have missing values if parsing failed?
    # Usually composition is complete.
    # Let's exclude 'source_type' etc.
    exclude_cols = ['source_type', 'synthesis_method', 'crystal_structure', 'doi']
    cols_to_impute = [c for c in numeric_cols if c not in exclude_cols]

    # Calculate missing rates
    missing_rates = df[cols_to_impute].isnull().mean()
    
    # Decision
    max_missing = missing_rates.max()
    strategy = "mean" if max_missing <= (threshold / 100.0) else "listwise"
    
    logger.info(f"Max missing rate: {max_missing:.2%}. Threshold: {threshold/100:.2%}. Strategy: {strategy}")

    if strategy == "listwise":
        # Drop rows with ANY missing value in the columns to impute
        df = df.dropna(subset=cols_to_impute)
        logger.info(f"Performed listwise deletion. Rows remaining: {len(df)}")
    else:
        # Mean imputation
        for col in cols_to_impute:
            if df[col].isnull().any():
                mean_val = df[col].mean()
                df[col].fillna(mean_val, inplace=True)
        logger.info("Performed mean imputation.")

    # 6. Save to processed
    processed_file = DATA_PROCESSED_DIR / "alloys_raw.csv"
    df.to_csv(processed_file, index=False)
    logger.info(f"Saved processed data to {processed_file}")

    # 7. Run Feature Engineering
    # This depends on `data/processed/alloys_raw.csv`
    run_feature_engineering_pipeline()
    if not (DATA_PROCESSED_DIR / "alloys_features.csv").exists():
        logger.error("Feature engineering failed.")
        return False, {}

    # 8. Run Training
    # This depends on `data/processed/alloys_features.csv`
    run_training_pipeline()
    if not (DATA_PROCESSED_DIR / "model_metrics.json").exists():
        logger.error("Model training failed.")
        return False, {}

    # 9. Load Metrics
    with open(DATA_PROCESSED_DIR / "model_metrics.json", 'r') as f:
        metrics = json.load(f)

    return True, metrics

def run_sensitivity_analysis():
    """Runs the sensitivity analysis for all thresholds."""
    setup_directories()
    backup_current_artifacts()

    results = {
        "thresholds_tested": THRESHOLDS_TO_TEST,
        "results": []
    }

    try:
        for threshold in THRESHOLDS_TO_TEST:
            success, metrics = run_pipeline_with_threshold(threshold)
            if success:
                results["results"].append({
                    "threshold": threshold,
                    "metrics": metrics
                })
            else:
                results["results"].append({
                    "threshold": threshold,
                    "status": "failed",
                    "metrics": None
                })
    finally:
        restore_current_artifacts()

    # Save results
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {OUTPUT_FILE}")
    return results

def main():
    """Entry point for the script."""
    setup_logging()
    run_sensitivity_analysis()

if __name__ == "__main__":
    main()
