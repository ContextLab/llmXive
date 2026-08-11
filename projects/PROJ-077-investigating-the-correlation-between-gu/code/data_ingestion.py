import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any

# Import existing utilities from sibling modules
from config import INPUT_PATHS, SAMPLE_LIMIT, RANDOM_SEED
from logging_config import get_logger, log_provenance, log_warning, log_imputation_strategy, log_data_filtering, log_pipeline_start, log_pipeline_end

logger = get_logger(__name__)

def check_dqs_availability(df: pd.DataFrame) -> bool:
    """Check if DQS column exists or if raw dietary columns are present."""
    if 'dqs' in df.columns:
        return True
    # Check for required raw dietary columns to calculate DQS
    required_cols = ['fruit', 'vegetable', 'whole_grain', 'dairy', 'protein', 'sodium']
    if all(col in df.columns for col in required_cols):
        return True
    return False

def calculate_dqs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate HEI-2015 Diet Quality Score (DQS) from raw dietary data.
    Components: Total Fruits (5), Whole Fruits (5), Total Vegetables (5),
    Greens and Beans (5), Whole Grains (10), Dairy (10), Total Protein (5),
    Seafood/Plant Proteins (5), Refined Grains (10), Sodium (10), Empty Calories (20).
    """
    logger.info("Calculating DQS using HEI-2015 standard formula")
    
    # Initialize score
    df['dqs'] = 0.0
    
    # Helper to cap values at max points
    def cap_score(series, max_pts):
        return series.clip(upper=max_pts)
    
    # 1. Total Fruits (0-5 pts) - based on 'fruit' column
    if 'fruit' in df.columns:
        # Simplified: linear scaling up to a threshold (e.g., 2 servings/day = 5 pts)
        df['dqs'] += cap_score(df['fruit'] * (5.0 / 2.0), 5)
    
    # 2. Whole Fruits (0-5 pts) - based on 'whole_fruit' if available, else same as fruit
    if 'whole_fruit' in df.columns:
        df['dqs'] += cap_score(df['whole_fruit'] * (5.0 / 2.0), 5)
    
    # 3. Total Vegetables (0-5 pts)
    if 'vegetable' in df.columns:
        df['dqs'] += cap_score(df['vegetable'] * (5.0 / 2.0), 5)
    
    # 4. Greens and Beans (0-5 pts)
    if 'greens_beans' in df.columns:
        df['dqs'] += cap_score(df['greens_beans'] * (5.0 / 2.0), 5)
    
    # 5. Whole Grains (0-10 pts)
    if 'whole_grain' in df.columns:
        df['dqs'] += cap_score(df['whole_grain'] * (10.0 / 3.0), 10)
    
    # 6. Dairy (0-10 pts)
    if 'dairy' in df.columns:
        df['dqs'] += cap_score(df['dairy'] * (10.0 / 3.0), 10)
    
    # 7. Total Protein Foods (0-5 pts)
    if 'protein' in df.columns:
        df['dqs'] += cap_score(df['protein'] * (5.0 / 5.0), 5)
    
    # 8. Seafood and Plant Proteins (0-5 pts)
    if 'seafood_plant_prot' in df.columns:
        df['dqs'] += cap_score(df['seafood_plant_prot'] * (5.0 / 2.5), 5)
    
    # 9. Refined Grains (0-10 pts) - Inverse: lower is better
    if 'refined_grain' in df.columns:
        # Assume max penalty at 4 servings, max reward at 0
        df['dqs'] += cap_score((4.0 - df['refined_grain']) * (10.0 / 4.0), 10)
    
    # 10. Sodium (0-10 pts) - Inverse
    if 'sodium' in df.columns:
        # Assume max penalty at 4000mg, max reward at 1100mg
        df['dqs'] += cap_score(((4000 - df['sodium']) / 2900) * 10, 10)
    
    # 11. Empty Calories (0-20 pts) - Inverse
    if 'empty_calories' in df.columns:
        # Assume max penalty at 500kcal, max reward at 0
        df['dqs'] += cap_score((1 - df['empty_calories']/500) * 20, 20)
    
    # Ensure non-negative
    df['dqs'] = df['dqs'].clip(lower=0)
    
    log_provenance(f"DQS calculated for {len(df)} participants using HEI-2015 formula")
    return df

def load_and_merge_data() -> pd.DataFrame:
    """
    Load raw microbiome and cognitive data from data/raw/ and merge by participant_id.
    Implements FR-001: Merge by participant_id.
    """
    logger.info("Starting data loading and merging")
    log_pipeline_start("data_ingestion")
    
    # Define paths
    microbiome_path = INPUT_PATHS.get('microbiome', 'data/raw/microbiome_data.csv')
    cognitive_path = INPUT_PATHS.get('cognitive', 'data/raw/cognitive_data.csv')
    dietary_path = INPUT_PATHS.get('dietary', 'data/raw/dietary_data.csv')
    
    # Load microbiome data
    if not os.path.exists(microbiome_path):
        raise FileNotFoundError(f"Microbiome data not found at {microbiome_path}")
    df_micro = pd.read_csv(microbiome_path)
    
    # Load cognitive data
    if not os.path.exists(cognitive_path):
        raise FileNotFoundError(f"Cognitive data not found at {cognitive_path}")
    df_cog = pd.read_csv(cognitive_path)
    
    # Merge on participant_id
    if 'participant_id' not in df_micro.columns or 'participant_id' not in df_cog.columns:
        raise ValueError("Both datasets must contain 'participant_id' column")
    
    df_merged = pd.merge(df_micro, df_cog, on='participant_id', how='inner')
    log_provenance(f"Merged {len(df_merged)} participants from microbiome and cognitive data")
    
    # Load dietary data if available and merge
    if os.path.exists(dietary_path):
        df_diet = pd.read_csv(dietary_path)
        df_merged = pd.merge(df_merged, df_diet, on='participant_id', how='left')
        log_provenance(f"Merged dietary data for {len(df_merged)} participants")
    
    return df_merged

def filter_primary_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out participants with null alpha diversity, fluid intelligence, or DQS.
    Implements User Story 1, FR-001.
    """
    logger.info("Filtering participants with missing primary outcomes")
    
    required_cols = ['shannon_index', 'fluid_intelligence']
    
    # Check if DQS is required (per FR-008)
    if 'dqs' not in df.columns:
        # Try to calculate if raw data exists
        if check_dqs_availability(df):
            df = calculate_dqs(df)
        else:
            raise ValueError("DQS column missing and raw dietary data unavailable. FR-008 requires DQS.")
    
    required_cols.append('dqs')
    
    # Filter rows where any required column is NaN
    initial_count = len(df)
    df_filtered = df.dropna(subset=required_cols)
    filtered_count = len(df_filtered)
    
    log_data_filtering(
        reason="Missing primary outcomes (shannon_index, fluid_intelligence, dqs)",
        removed=initial_count - filtered_count,
        remaining=filtered_count
    )
    
    if filtered_count == 0:
        raise ValueError("No participants remaining after filtering primary outcomes.")
    
    return df_filtered

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Median for Age, BMI, DQS; Mode for Sex.
    Implements Plan logic: Median for numeric, Mode for categorical.
    Logs imputation strategy to provenance.log.
    """
    logger.info("Starting imputation of missing values")
    
    # Define numeric columns for median imputation
    numeric_cols = ['age', 'bmi', 'dqs']
    # Define categorical columns for mode imputation
    categorical_cols = ['sex']
    
    imputation_log = []
    
    # Impute numeric columns with Median
    for col in numeric_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                imputation_log.append(f"Column '{col}': Imputed {missing_count} NaNs with Median ({median_val:.2f})")
                log_imputation_strategy(column=col, strategy="median", value=median_val, count=missing_count)
    
    # Impute categorical columns with Mode
    for col in categorical_cols:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                # Get the most frequent value (mode)
                mode_val = df[col].mode()[0]
                df[col] = df[col].fillna(mode_val)
                imputation_log.append(f"Column '{col}': Imputed {missing_count} NaNs with Mode ('{mode_val}')")
                log_imputation_strategy(column=col, strategy="mode", value=mode_val, count=missing_count)
    
    # Log summary
    log_provenance("Imputation completed. Strategies applied: Median for numeric (age, bmi, dq), Mode for categorical (sex).")
    logger.info(f"Imputation summary: {imputation_log}")
    
    return df

def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Orchestrate the full data ingestion pipeline:
    1. Load and merge data
    2. Filter primary outcomes
    3. Impute missing values
    """
    logger.info("Running full data ingestion pipeline")
    
    # Step 1: Load and merge
    df = load_and_merge_data()
    
    # Step 2: Filter primary outcomes
    df = filter_primary_outcomes(df)
    
    # Step 3: Impute missing values
    df = impute_missing_values(df)
    
    log_pipeline_end("data_ingestion", rows=len(df))
    return df

def main():
    """Entry point for data ingestion script."""
    try:
        df = run_ingestion_pipeline()
        logger.info(f"Pipeline complete. Processed {len(df)} participants.")
        return df
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()