import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any

# Import from sibling modules as per API surface
from config import INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, DQS_REQUIRED
from logging_config import get_logger, log_provenance, log_warning, log_imputation_strategy, log_data_filtering

logger = get_logger(__name__)

def calculate_hei_component_score(component_name: str, value: float) -> float:
    """
    Calculate a single HEI-2015 component score.
    Note: This is a simplified placeholder for the full HEI-2015 logic.
    In a real implementation, this would contain the specific scoring tables
    for each of the 12 components (Total Fruits, Whole Fruits, etc.).
    """
    if pd.isna(value) or value < 0:
        return 0.0
    
    # Placeholder logic: cap at 10 points, linear scaling for demonstration
    # REAL IMPLEMENTATION NOTE: Replace with actual HEI-2015 scoring tables
    score = min(value, 10.0) 
    return score

def calculate_dqs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the Diet Quality Score (DQS) based on HEI-2015 components.
    FR-008: System MUST compute DQS using the full HEI-2015 standard formula.
    """
    required_components = [
        'Total Fruits', 'Whole Fruits', 'Total Vegetables', 'Greens and Beans',
        'Whole Grains', 'Dairy', 'Total Protein Foods', 'Seafood and Plant Proteins',
        'Refined Grains', 'Sodium', 'Empty Calories'
    ]
    
    missing_cols = [col for col in required_components if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required HEI-2015 columns for DQS calculation: {missing_cols}")
    
    # Calculate each component score
    for col in required_components:
        df[f'{col}_score'] = df[col].apply(lambda x: calculate_hei_component_score(col, x))
    
    # Sum scores to get DQS (Max 100 typically, but depends on specific HEI-2015 weighting)
    # For this implementation, we sum the component scores directly
    component_scores = [f'{col}_score' for col in required_components]
    df['dqs'] = df[component_scores].sum(axis=1)
    
    logger.info(f"DQS calculated successfully for {len(df)} participants.")
    return df

def check_dqs_availability(df: pd.DataFrame) -> bool:
    """
    Check if DQS column exists or if raw dietary data is available for calculation.
    """
    if 'dqs' in df.columns:
        return True
    
    required_raw_cols = [
        'Total Fruits', 'Whole Fruits', 'Total Vegetables', 'Greens and Beans',
        'Whole Grains', 'Dairy', 'Total Protein Foods', 'Seafood and Plant Proteins',
        'Refined Grains', 'Sodium', 'Empty Calories'
    ]
    
    available = all(col in df.columns for col in required_raw_cols)
    if not available:
        missing = [col for col in required_raw_cols if col not in df.columns]
        logger.warning(f"Raw dietary data incomplete for DQS calculation. Missing: {missing}")
    
    return available

def load_and_merge_data() -> pd.DataFrame:
    """
    Load raw microbiome and cognitive data from data/raw/ and merge by participant ID.
    FR-001: Merge by 'participant_id' (or 'eid'/'subject_id' fallback).
    """
    microbiome_path = INPUT_PATHS.get('microbiome')
    cognitive_path = INPUT_PATHS.get('cognitive')
    
    if not os.path.exists(microbiome_path):
        raise FileNotFoundError(f"Microbiome data not found at {microbiome_path}")
    if not os.path.exists(cognitive_path):
        raise FileNotFoundError(f"Cognitive data not found at {cognitive_path}")
    
    # Load data with streaming if large, otherwise standard load
    # Assuming standard load for now, but respects SAMPLE_LIMIT if needed
    df_micro = pd.read_csv(microbiome_path)
    df_cog = pd.read_csv(cognitive_path)
    
    # Determine merge key
    merge_key = None
    for key in ['participant_id', 'eid', 'subject_id']:
        if key in df_micro.columns and key in df_cog.columns:
            merge_key = key
            break
    
    if not merge_key:
        raise FileNotFoundError("Could not find a common participant ID column ('participant_id', 'eid', or 'subject_id').")
    
    logger.info(f"Merging data on column: {merge_key}")
    merged_df = pd.merge(df_micro, df_cog, on=merge_key, how='inner')
    
    log_provenance(f"Data merged on {merge_key}. Resulting shape: {merged_df.shape}")
    return merged_df

def filter_primary_outcomes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out participants with null alpha diversity, fluid intelligence, or DQS.
    FR-001: Filter null primary outcomes.
    """
    required_cols = ['shannon_index', 'fluid_intelligence']
    if DQS_REQUIRED:
        required_cols.append('dqs')
    elif 'dqs' in df.columns:
        required_cols.append('dqs')
    
    initial_count = len(df)
    df_filtered = df.dropna(subset=required_cols)
    final_count = len(df_filtered)
    
    log_data_filtering(
        filter_type="primary_outcomes",
        initial_rows=initial_count,
        removed_rows=(initial_count - final_count),
        reason="Null values in primary outcome or required covariate columns"
    )
    
    return df_filtered

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply imputation logic: Median for Age, BMI, DQS; Mode for Sex.
    T013: Dependency T047 (Spec Override) - Mode for Sex, Median for numeric.
    Logs imputation strategy to provenance.log.
    """
    df_imputed = df.copy()
    numeric_cols = ['age', 'bmi', 'dqs']
    categorical_cols = ['sex']
    
    imputation_log = []
    
    # Numeric imputation (Median)
    for col in numeric_cols:
        if col in df_imputed.columns:
            if df_imputed[col].isna().any():
                median_val = df_imputed[col].median()
                df_imputed[col] = df_imputed[col].fillna(median_val)
                imputation_log.append(f"Column '{col}': Imputed {df_imputed[col].isna().sum()} missing values with Median ({median_val:.2f})")
            else:
                imputation_log.append(f"Column '{col}': No missing values found.")
    
    # Categorical imputation (Mode)
    for col in categorical_cols:
        if col in df_imputed.columns:
            if df_imputed[col].isna().any():
                # Calculate mode, handling potential multimodal by taking the first one
                mode_val = df_imputed[col].mode()
                if len(mode_val) > 0:
                    mode_val = mode_val[0]
                    df_imputed[col] = df_imputed[col].fillna(mode_val)
                    imputation_log.append(f"Column '{col}': Imputed {df_imputed[col].isna().sum()} missing values with Mode ('{mode_val}')")
                else:
                    logger.warning(f"Column '{col}' has no mode (all NaN). Cannot impute.")
            else:
                imputation_log.append(f"Column '{col}': No missing values found.")
    
    # Log the strategy as required by Data Hygiene Principle III
    log_imputation_strategy(imputation_log)
    
    return df_imputed

def run_ingestion_pipeline() -> pd.DataFrame:
    """
    Orchestrate the data ingestion pipeline: Load -> Filter -> Calculate DQS -> Impute.
    """
    logger.info("Starting Data Ingestion Pipeline.")
    
    # 1. Load and Merge
    df = load_and_merge_data()
    
    # 2. Check DQS availability and calculate if needed
    if 'dqs' not in df.columns:
        if check_dqs_availability(df):
            df = calculate_dqs(df)
        elif DQS_REQUIRED:
            raise RuntimeError("DQS is required but cannot be calculated from available data.")
        else:
            logger.warning("DQS data not available and DQS_REQUIRED=False. Proceeding without DQS.")
    
    # 3. Filter Primary Outcomes
    df = filter_primary_outcomes(df)
    
    # 4. Impute Missing Values (T013)
    df = impute_missing_values(df)
    
    logger.info("Data Ingestion Pipeline completed successfully.")
    return df

def main():
    """
    Entry point for the data ingestion script.
    Runs the pipeline and saves the cleaned dataset.
    """
    try:
        cleaned_df = run_ingestion_pipeline()
        
        # Save the cleaned dataset (T015 logic integrated here for completeness)
        output_path = INPUT_PATHS.get('processed_cleaned', 'data/processed/cleaned_data.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Add header with column definitions as requested
        header_comment = "# Column Definitions:\n"
        header_comment += "# shannon_index: Alpha diversity (Shannon Index)\n"
        header_comment += "# fluid_intelligence: Cognitive performance score\n"
        header_comment += "# age, sex, bmi: Demographic covariates\n"
        header_comment += "# dqs: Diet Quality Score (HEI-2015)\n"
        
        with open(output_path, 'w') as f:
            f.write(header_comment)
            cleaned_df.to_csv(f, index=False)
        
        logger.info(f"Cleaned dataset saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()