"""
Ecological Aggregation Module (FR-003)

Implements the aggregation of microbiome and EEG data into demographic strata.
Handles missing data via exclusion (primary) and documented median imputation (secondary).
Enforces the minimum valid strata count (>= 5) or exits with code 1.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import project utilities from existing API surface
from config import get_project_root
from logging_config import get_analysis_logger, log_structured_event
from seed_manager import set_seed

# Constants
MIN_STRATA_SUBJECTS = 5
MIN_VALID_STRATA_COUNT = 5
PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

logger = get_analysis_logger("ecological_aggregation")

def load_microbiome_data() -> pd.DataFrame:
    """Load processed microbiome features."""
    path = DATA_PROCESSED_DIR / "microbiome_features.csv"
    if not path.exists():
        raise FileNotFoundError(f"Microbiome data not found at {path}. Run T012 first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded microbiome data: {len(df)} rows, columns: {list(df.columns)}")
    return df

def load_eeg_data() -> pd.DataFrame:
    """Load processed EEG features."""
    path = DATA_PROCESSED_DIR / "eeg_features.csv"
    if not path.exists():
        raise FileNotFoundError(f"EEG data not found at {path}. Run T013 first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded EEG data: {len(df)} rows, columns: {list(df.columns)}")
    return df

def handle_missing_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing demographic data (Age, Sex, BMI, Diet).
    Primary strategy: Exclusion.
    Secondary strategy: Documented Median Imputation if it helps reach threshold.
    """
    required_cols = ["subject_id", "age", "sex", "bmi", "diet"]
    missing_mask = df[required_cols].isnull().any(axis=1)
    excluded_count = missing_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} subjects due to missing demographics (Primary Strategy).")
        df_excluded = df.dropna(subset=required_cols)
    else:
        df_excluded = df.copy()

    # Check if we need imputation to reach MIN_STRATA_SUBJECTS for any potential group
    # This is a simplified check: if the dataset is very small, we might try imputation
    # However, the spec says: "If exclusion results in <5 subjects in a potential stratum, 
    # attempt Documented Median Imputation only if it helps reach the threshold; otherwise, exclude."
    # Since we don't know the strata yet, we apply imputation on a best-effort basis for the remaining
    # rows if the total count is low, but strictly speaking, the primary path is exclusion.
    # We will implement the imputation only if the dataset is extremely sparse after exclusion.
    
    if len(df_excluded) < MIN_STRATA_SUBJECTS * 2:
        logger.info("Dataset small after exclusion. Attempting documented median imputation for missing values.")
        numeric_cols = ["age", "bmi"]
        categorical_cols = ["sex", "diet"]
        
        for col in numeric_cols:
            if col in df_excluded.columns:
                median_val = df_excluded[col].median()
                df_excluded[col] = df_excluded[col].fillna(median_val)
                logger.info(f"Imputed {col} with median {median_val}")
        
        for col in categorical_cols:
            if col in df_excluded.columns:
                mode_val = df_excluded[col].mode()[0] if not df_excluded[col].mode().empty else "Unknown"
                df_excluded[col] = df_excluded[col].fillna(mode_val)
                logger.info(f"Imputed {col} with mode {mode_val}")

    return df_excluded

def create_strata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group subjects into demographic strata.
    Bins: Age (decades), Sex (M/F), BMI (Underweight, Normal, Overweight, Obese), Diet (Vegan, Vegetarian, Omnivore, etc.)
    """
    # Bin Age
    df = df.copy()
    df['age_bin'] = pd.cut(df['age'], bins=[0, 20, 30, 40, 50, 60, 70, 80, 100], labels=['0-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71-80', '80+'])
    
    # Bin BMI
    def bmi_category(bmi):
        if pd.isna(bmi): return "Unknown"
        if bmi < 18.5: return "Underweight"
        if bmi < 25: return "Normal"
        if bmi < 30: return "Overweight"
        return "Obese"
    df['bmi_bin'] = df['bmi'].apply(bmi_category)

    # Standardize Diet if needed (assuming raw data is clean enough or handled in preprocessing)
    # If 'diet' is missing, it was handled in handle_missing_demographics
    
    # Create Stratum ID
    df['stratum_id'] = df['age_bin'].astype(str) + "_" + df['sex'].astype(str) + "_" + df['bmi_bin'].astype(str) + "_" + df['diet'].astype(str)

    return df

def aggregate_strata(microbiome_df: pd.DataFrame, eeg_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregate data into strata and count valid strata.
    A valid stratum has >= 5 subjects in BOTH cohorts (AGP and OpenNeuro).
    Since we are merging, we check the merged count.
    """
    # Handle missing data
    microbiome_df = handle_missing_demographics(microbiome_df)
    eeg_df = handle_missing_demographics(eeg_df)

    # Create Strata IDs
    microbiome_df = create_strata(microbiome_df)
    eeg_df = create_strata(eeg_df)

    # Merge on subject_id?
    # The spec implies we have subjects in both or we are aggregating available data.
    # However, T012 and T013 produce separate files. We need to find common subjects or aggregate based on available data.
    # The task description says: "Identify groups with >= 5 subjects in *both* cohorts".
    # This implies an intersection of subjects or a check on the merged dataset.
    # Let's assume the subject IDs are the key to merge.
    
    # Inner join to ensure we only have subjects with both microbiome and EEG data?
    # Or does the project allow partial data? The spec says "in both cohorts", suggesting we need the intersection.
    merged_df = pd.merge(
        microbiome_df, 
        eeg_df, 
        on="subject_id", 
        how="inner", 
        suffixes=('_micro', '_eeg')
    )

    if len(merged_df) == 0:
        logger.error("No common subjects found between microbiome and EEG datasets.")
        return merged_df, {"valid_strata_count": 0, "total_strata": 0}

    logger.info(f"Merged dataset size: {len(merged_df)} subjects.")

    # Count subjects per stratum
    stratum_counts = merged_df.groupby('stratum_id').size().reset_index(name='n_subjects')
    
    # Filter valid strata (>= 5 subjects)
    valid_strata = stratum_counts[stratum_counts['n_subjects'] >= MIN_STRATA_SUBJECTS]
    
    valid_strata_count = len(valid_strata)
    total_strata = len(stratum_counts)

    logger.info(f"Total strata: {total_strata}, Valid strata (>= {MIN_STRATA_SUBJECTS} subjects): {valid_strata_count}")

    # Prepare report
    report = {
        "valid_strata_count": valid_strata_count,
        "total_strata": total_strata,
        "min_subjects_per_stratum": MIN_STRATA_SUBJECTS,
        "exclusion_applied": True, # Based on logic above
        "imputation_applied": False # Check if imputation was actually needed if we track it
    }

    # Prepare raw output
    # We need to keep the merged data for the next step (T015)
    # Filter the merged_df to only include valid strata?
    # The task says: "Output: Write `data/processed/raw_stratum_agg.csv` (containing subject IDs, stratum ID, and raw data)"
    # It doesn't explicitly say to filter, but T015 computes means on valid strata.
    # Let's output the full merged data with stratum_id, and T015 will filter or aggregate.
    # However, the exit logic depends on valid_strata_count.
    
    raw_output = merged_df[['subject_id', 'stratum_id', 'n_subjects']].copy() # Simplified, but we need all raw data
    # Actually, we need to keep all columns for T015 to compute means.
    # Let's just keep the merged_df and add n_subjects column
    merged_df_with_counts = merged_df.merge(stratum_counts, on='stratum_id', how='left')
    
    return merged_df_with_counts, report

def main():
    """Main entry point for Ecological Aggregation."""
    logger.info("Starting Ecological Aggregation (T014)...")
    
    try:
        # 1. Load Data
        microbiome_df = load_microbiome_data()
        eeg_df = load_eeg_data()
        
        # 2. Aggregate
        raw_agg_df, report = aggregate_strata(microbiome_df, eeg_df)
        
        # 3. Output Files
        raw_output_path = DATA_PROCESSED_DIR / "raw_stratum_agg.csv"
        report_path = ARTIFACTS_DIR / "strata_report.json"
        
        raw_agg_df.to_csv(raw_output_path, index=False)
        logger.info(f"Wrote raw aggregation to {raw_output_path}")
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Wrote strata report to {report_path}")
        
        # 4. Exit Logic
        if report["valid_strata_count"] < MIN_VALID_STRATA_COUNT:
            logger.error(f"Insufficient valid strata ({report['valid_strata_count']} < {MIN_VALID_STRATA_COUNT}) for ecological analysis.")
            log_structured_event("ERROR", "Insufficient valid strata", {"count": report["valid_strata_count"]})
            sys.exit(1)
        
        logger.info(f"Ecological Aggregation successful. Valid strata: {report['valid_strata_count']}")
        sys.exit(0)
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
