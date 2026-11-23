import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any
from config import INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, DQS_REQUIRED
from logging_config import get_logger, log_operation, log_pipeline_start, log_pipeline_end, log_provenance, log_warning
from data_utils import load_chunked, load_csv_streaming

logger = get_logger("data_ingestion")

def load_and_merge_data():
    """
    Load raw microbiome, cognitive, and dietary data and merge them.
    
    Returns:
        pd.DataFrame: Merged dataset.
    """
    log_pipeline_start("Data Ingestion")
    
    try:
        # Load individual datasets
        microbiome_df = load_csv_streaming(INPUT_PATHS["microbiome"])
        cognitive_df = load_csv_streaming(INPUT_PATHS["cognitive"])
        dietary_df = load_csv_streaming(INPUT_PATHS["dietary"])
        
        # Fallback ID column names
        id_cols = ['participant_id', 'eid', 'subject_id']
        
        def get_id_col(df, cols=id_cols):
            for c in cols:
                if c in df.columns:
                    return c
            return None
        
        # Merge logic
        merged = microbiome_df
        
        # Merge with cognitive
        cog_id = get_id_col(cognitive_df)
        if cog_id:
            merged = pd.merge(merged, cognitive_df, left_on=get_id_col(merged), right_on=cog_id, how='inner')
        else:
            log_warning("Cognitive data missing ID column, skipping merge.")
            
        # Merge with dietary
        diet_id = get_id_col(dietary_df)
        if diet_id:
            merged = pd.merge(merged, dietary_df, left_on=get_id_col(merged), right_on=diet_id, how='inner')
        else:
            log_warning("Dietary data missing ID column, skipping merge.")
            
        # Normalize ID column name
        if get_id_col(merged) and get_id_col(merged) != 'participant_id':
            merged = merged.rename(columns={get_id_col(merged): 'participant_id'})
            
        return merged
        
    except Exception as e:
        log_warning(f"Data loading failed: {e}")
        raise

def filter_primary_outcomes(df):
    """
    Filter out participants with missing primary outcomes.
    Primary outcomes: shannon_index, fluid_intelligence_score.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    required_cols = ['shannon_index', 'fluid_intelligence_score']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        log_warning(f"Missing required outcome columns: {missing_cols}. Attempting to proceed with available columns.")
        required_cols = [c for c in required_cols if c in df.columns]
        
    if not required_cols:
        log_warning("No primary outcome columns found. Returning original data.")
        return df
        
    initial_rows = len(df)
    df = df.dropna(subset=required_cols)
    final_rows = len(df)
    
    log_provenance(f"Filtered {initial_rows - final_rows} rows with missing primary outcomes.")
    return df

def impute_missing_values(df):
    """
    Impute missing values: Median for Age, BMI, DQS; Mode for Sex.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        pd.DataFrame: Imputed DataFrame.
    """
    df = df.copy()
    
    # Define imputation rules
    median_cols = ['age', 'bmi', 'dietary_quality_score']
    mode_cols = ['sex']
    
    for col in median_cols:
        if col in df.columns and df[col].isnull().any():
            median_val = df[col].median()
            df[col].fillna(median_val, inplace=True)
            log_provenance(f"Imputed {col} with median: {median_val}")
            
    for col in mode_cols:
        if col in df.columns and df[col].isnull().any():
            mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
            df[col].fillna(mode_val, inplace=True)
            log_provenance(f"Imputed {col} with mode: {mode_val}")
            
    return df

def save_cleaned_dataset(df, output_path="data/processed/cleaned_data.csv"):
    """
    Save the cleaned dataset to CSV.
    
    Args:
        df: Cleaned DataFrame.
        output_path: Path to save the CSV.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log_provenance(f"Cleaned dataset saved to {output_path}")

def run_ingestion_pipeline():
    """Run the full data ingestion pipeline."""
    log_pipeline_start("Ingestion Pipeline")
    
    try:
        # 1. Load and Merge
        df = load_and_merge_data()
        
        # 2. Filter
        df = filter_primary_outcomes(df)
        
        # 3. Impute
        df = impute_missing_values(df)
        
        # 4. Save
        save_cleaned_dataset(df)
        
        log_pipeline_end("Ingestion Pipeline completed.")
        return df
        
    except Exception as e:
        log_pipeline_end("Ingestion Pipeline failed.", error=str(e))
        raise

def main():
    """Entry point for data ingestion."""
    run_ingestion_pipeline()

if __name__ == "__main__":
    main()
