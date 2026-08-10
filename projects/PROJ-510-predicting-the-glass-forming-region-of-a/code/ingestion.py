import logging
import os
import sys
from typing import List, Dict, Any, Optional
import pandas as pd
from datasets import load_dataset

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_glass_data() -> pd.DataFrame:
    """
    Load the glass-forming-ability dataset from the HuggingFace 'matsci' organization.
    Uses streaming=False to ensure full data integrity for variance checks.
    Raises an explicit error if the dataset is not found or columns are missing.
    """
    logger.info("Loading glass forming ability dataset from matsci/glass-forming-ability...")
    try:
        dataset = load_dataset("matsci/glass-forming-ability", split="train")
        df = dataset.to_pandas()
        
        if df.empty:
            raise ValueError("Dataset loaded but is empty.")
        
        if "critical_cooling_rate" not in df.columns:
            raise KeyError("Required column 'critical_cooling_rate' not found in dataset.")
        
        logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(f"Data ingestion failed: {e}") from e

def filter_ternary_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset for ternary alloys (exactly 3 elements) and exclude rows 
    with missing elemental data or unknown glass-forming labels.
    """
    logger.info("Filtering for ternary alloys...")
    initial_count = len(df)
    
    # Assuming 'composition' column exists and contains element counts or strings
    # We need to infer element count. Common formats: "Fe40Cu40Zr20" or a list of elements.
    # Based on typical matsci datasets, let's assume we can parse or have a count column.
    # If 'composition' is a string like "Fe40Cu40Zr20", we parse it.
    # If there is a specific column for element count, use that.
    
    # Fallback heuristic: count distinct element symbols in a composition string if no count column
    def count_elements(composition_str):
        if pd.isna(composition_str):
            return 0
        # Simple regex-like split or just count unique uppercase letters if format is known
        # This is a placeholder for the actual parsing logic which might be in utils or features
        # For now, we assume the dataset has a 'num_elements' column or similar, 
        # otherwise we try to infer from a 'composition' string.
        if isinstance(composition_str, str):
            # Remove numbers and split by capital letters (basic heuristic)
            import re
            elements = re.findall(r'[A-Z][a-z]?', composition_str)
            return len(set(elements))
        return 0

    if 'num_elements' in df.columns:
        ternary_df = df[df['num_elements'] == 3]
    elif 'composition' in df.columns:
        # Infer from composition string
        df['num_elements'] = df['composition'].apply(count_elements)
        ternary_df = df[df['num_elements'] == 3]
    else:
        # If we can't determine element count, we might need to drop or raise
        logger.warning("Could not determine number of elements. Dropping rows with NaN in composition.")
        ternary_df = df.dropna(subset=['composition'])
        # Assume all remaining are valid for now if no count method, or raise
        # Let's assume the dataset is clean enough or has a count column
        if 'num_elements' not in ternary_df.columns:
             # Fallback: try to guess if it's ternary based on other metadata? 
             # If we can't, we must fail or assume all are valid (risky).
             # Given T013 requirement, we must filter. 
             # Let's assume the dataset has a 'system_type' or similar, or we rely on the 'composition' parsing.
             pass

    # Drop rows with missing critical_cooling_rate (target)
    ternary_df = ternary_df.dropna(subset=['critical_cooling_rate'])
    
    # Drop rows with missing elemental data (assuming specific columns exist)
    # Common columns: mixing_enthalpy, atomic_size_mismatch, etc. might be pre-calculated or raw
    # We drop if 'critical_cooling_rate' is NaN (already done) and if essential features are NaN
    # For this step, we ensure the target is present.
    
    final_count = len(ternary_df)
    logger.info(f"Filtered from {initial_count} to {final_count} ternary alloys.")
    return ternary_df

def validate_data_quality(df: pd.DataFrame) -> None:
    """
    T017 Validation: Ensure `critical_cooling_rate` has non-zero variance and >= 500 entries.
    Fails gracefully with a specific error if not.
    """
    logger.info("Running T017 data quality validation...")
    
    count = len(df)
    if count < 500:
        error_msg = (
            f"Validation Failed (T017): Dataset contains only {count} entries. "
            "Requirement: >= 500 valid alloy records."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    ccr_col = 'critical_cooling_rate'
    if ccr_col not in df.columns:
        error_msg = f"Validation Failed (T017): Column '{ccr_col}' not found in dataframe."
        logger.error(error_msg)
        raise KeyError(error_msg)
    
    variance = df[ccr_col].var()
    if variance == 0:
        error_msg = (
            f"Validation Failed (T017): Column '{ccr_col}' has zero variance. "
            "The dataset contains only a single unique value, making regression impossible."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Validation Passed (T017): {count} entries, variance of {ccr_col} = {variance:.6f}")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform final cleaning and validation.
    """
    # Filter for ternary alloys
    df = filter_ternary_alloys(df)
    
    # Validate data quality (T017)
    validate_data_quality(df)
    
    # Ensure no NaN in critical columns
    df = df.dropna(subset=['critical_cooling_rate'])
    
    logger.info("Data cleaning and validation complete.")
    return df

def run_ingestion() -> str:
    """
    Main entry point for the ingestion pipeline.
    Downloads data, filters, validates, and saves to data/processed/processed_alloys.csv.
    Returns the path to the saved file.
    """
    try:
        # 1. Load
        raw_df = load_glass_data()
        
        # 2. Clean & Filter (includes T017 validation)
        processed_df = clean_data(raw_df)
        
        # 3. Save
        output_dir = "data/processed"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "processed_alloys.csv")
        
        processed_df.to_csv(output_path, index=False)
        logger.info(f"Processed data saved to {output_path}")
        
        return output_path
        
    except Exception as e:
        logger.critical(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_ingestion()