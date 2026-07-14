"""
Data Ingestion Module.
Handles loading, merging, filtering, and imputation of microbiome and cognitive data.

Implements T011, T012, T013, T014a, T014b.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any

# Ensure imports work when run as script or module
if 'code' in os.getcwd():
    sys.path.insert(0, os.getcwd())
else:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root / 'code'))

from config import INPUT_PATHS, SAMPLE_LIMIT, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning, log_imputation_strategy, log_data_filtering
from data_utils import load_csv_with_dtypes

logger = get_logger()

def check_dqs_availability() -> bool:
    """
    T014a: Check if raw dietary data is present for DQS calculation.
    Returns True if dietary data is found, False otherwise.
    """
    # Check for specific file or columns in main dataset if dietary is merged
    dietary_file = INPUT_PATHS.get('dietary')
    if dietary_file and os.path.exists(dietary_file):
        logger.info("Dietary data file found. DQS calculation available.")
        return True
    
    # Fallback: check if main data has dietary columns
    main_file = INPUT_PATHS.get('microbiome') or INPUT_PATHS.get('cognitive')
    if main_file and os.path.exists(main_file):
        try:
            # Load a sample to check columns
            df = pd.read_csv(main_file, nrows=5)
            dietary_cols = [c for c in df.columns if c.lower() in ['fruit', 'vegetable', 'grain', 'sugar', 'meat']]
            if dietary_cols:
                logger.info("Dietary columns found in main dataset. DQS calculation available.")
                return True
        except Exception as e:
            log_warning(f"Could not check dietary columns in {main_file}: {e}")
    
    logger.info("No dietary data found. DQS calculation not available.")
    return False

def calculate_dqs(df: pd.DataFrame) -> pd.Series:
    """
    T014a: Calculate DQS (Dietary Quality Score) using HEI-2015 standard.
    Simplified implementation: Sum of normalized fruit, vegetable, grain, dairy, protein scores.
    """
    # Placeholder for HEI-2015 logic. In a real scenario, this would implement
    # the specific scoring criteria for each component.
    # Assuming columns exist: 'fruit', 'vegetable', 'grain', 'dairy', 'protein'
    components = ['fruit', 'vegetable', 'grain', 'dairy', 'protein']
    available_components = [c for c in components if c in df.columns]
    
    if not available_components:
        log_warning("No dietary components found for DQS calculation.")
        return pd.Series([np.nan] * len(df))
    
    # Normalize each component (0-10 scale) - simplified linear scaling
    # Real HEI-2015 has complex density and ratio rules
    dqs = pd.Series(0.0, index=df.index)
    for col in available_components:
        # Assume input is in grams/servings, normalize to 0-10
        # This is a placeholder normalization
        max_val = df[col].quantile(0.95) if df[col].max() > 0 else 1
        if max_val == 0: max_val = 1
        score = (df[col] / max_val) * 10
        score = score.clip(0, 10)
        dqs += score
    
    # Normalize total to 0-100
    dqs = (dqs / (len(available_components) * 10)) * 100
    return dqs

def load_and_merge_data() -> pd.DataFrame:
    """
    T011: Load raw microbiome and cognitive data and merge by participant_id.
    """
    microbiome_path = INPUT_PATHS.get('microbiome')
    cognitive_path = INPUT_PATHS.get('cognitive')
    
    if not microbiome_path or not os.path.exists(microbiome_path):
        raise FileNotFoundError(f"Microbiome data file not found: {microbiome_path}")
    if not cognitive_path or not os.path.exists(cognitive_path):
        raise FileNotFoundError(f"Cognitive data file not found: {cognitive_path}")

    logger.info(f"Loading microbiome data from {microbiome_path}")
    df_micro = load_csv_with_dtypes(microbiome_path, chunksize=10000)
    # Concatenate chunks if necessary, or just load first chunk for demo if file is small
    # For robustness, we assume load_csv_with_dtypes returns a full DF or we handle chunks
    # Here we assume it returns a DF for simplicity in this context
    if isinstance(df_micro, pd.DataFrame):
        pass
    else:
        # Fallback if it returns an iterator
        chunks = []
        for chunk in df_micro:
            chunks.append(chunk)
        df_micro = pd.concat(chunks, ignore_index=True)

    logger.info(f"Loading cognitive data from {cognitive_path}")
    df_cog = load_csv_with_dtypes(cognitive_path, chunksize=10000)
    if isinstance(df_cog, pd.DataFrame):
        pass
    else:
        chunks = []
        for chunk in df_cog:
            chunks.append(chunk)
        df_cog = pd.concat(chunks, ignore_index=True)

    # Limit sample size if specified
    if SAMPLE_LIMIT and len(df_micro) > SAMPLE_LIMIT:
        df_micro = df_micro.sample(n=SAMPLE_LIMIT, random_state=RANDOM_SEED)
    if SAMPLE_LIMIT and len(df_cog) > SAMPLE_LIMIT:
        df_cog = df_cog.sample(n=SAMPLE_LIMIT, random_state=RANDOM_SEED)

    # Merge
    merged_df = pd.merge(df_micro, df_cog, on='participant_id', how='inner')
    log_provenance(f"Merged datasets. Resulting shape: {merged_df.shape}")
    return merged_df

def filter_primary_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    T012: Filter out participants with null alpha diversity, fluid intelligence, or DQS.
    """
    initial_count = len(df)
    
    # Define required columns based on spec
    required_cols = ['shannon_index', 'fluid_intelligence']
    
    # Check if DQS is required (FR-008)
    dqs_available = check_dqs_availability()
    if dqs_available:
        required_cols.append('dqs')
        log_data_filtering("DQS is available; filtering rows with null DQS.")
    else:
        # If DQS not available but required by FR-008, this should be handled by T014b
        # T014b ensures we don't reach here if DQS is mandatory but missing
        log_warning("DQS not available. Proceeding without DQS filtering if not strictly required.")

    # Filter
    mask = df[required_cols].notnull().all(axis=1)
    filtered_df = df[mask]
    
    final_count = len(filtered_df)
    log_data_filtering(f"Filtered {initial_count - final_count} rows with null primary outcomes.")
    return filtered_df

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    T013: Impute missing values.
    - Median for Age, BMI, DQS
    - Mode for Sex
    """
    df_imputed = df.copy()
    
    # Numeric columns: Median
    numeric_cols = ['age', 'bmi', 'dqs']
    for col in numeric_cols:
        if col in df_imputed.columns:
            median_val = df_imputed[col].median()
            if pd.isna(median_val):
                log_warning(f"Median for {col} is NaN. Skipping imputation.")
                continue
            count_null = df_imputed[col].isna().sum()
            if count_null > 0:
                df_imputed[col] = df_imputed[col].fillna(median_val)
                log_imputation_strategy(f"Imputed {count_null} nulls in {col} with median {median_val:.2f}")

    # Categorical columns: Mode
    categorical_cols = ['sex']
    for col in categorical_cols:
        if col in df_imputed.columns:
            mode_val = df_imputed[col].mode()
            if len(mode_val) > 0:
                mode_val = mode_val[0]
                count_null = df_imputed[col].isna().sum()
                if count_null > 0:
                    df_imputed[col] = df_imputed[col].fillna(mode_val)
                    log_imputation_strategy(f"Imputed {count_null} nulls in {col} with mode '{mode_val}'")
            else:
                log_warning(f"No mode found for {col}. Cannot impute.")

    return df_imputed

def run_ingestion_pipeline() -> Optional[pd.DataFrame]:
    """
    Orchestrates the full ingestion pipeline: Load -> Merge -> Filter -> Impute.
    Returns the cleaned DataFrame.
    """
    try:
        # T014b: Check DQS availability and fail if required but missing
        # Assuming FR-008 makes DQS mandatory. If not available, we stop.
        dqs_available = check_dqs_availability()
        # If the spec says DQS is MUST, we raise here if not found.
        # For this implementation, we assume DQS is required per FR-008.
        if not dqs_available:
            raise RuntimeError("DQS calculation required (FR-008) but dietary data not found. Halting pipeline.")

        # T011: Load and Merge
        df = load_and_merge_data()

        # Calculate DQS if needed
        if 'dqs' not in df.columns and dqs_available:
            df['dqs'] = calculate_dqs(df)

        # T012: Filter
        df = filter_primary_outcomes(df)

        # T013: Impute
        df = impute_missing_values(df)

        log_provenance("Ingestion pipeline completed successfully.")
        return df

    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        return None
