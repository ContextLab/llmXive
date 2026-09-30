"""
T016: Create Cleaned Dataset
Implements the creation of the intermediate cleaned dataset in data/interim/cleaned_adress.csv.
Depends on T014 (Filter Records) and T015 (Metadata Extraction).
"""
import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from config import get_path, ensure_dirs
from utils import get_logger

logger = get_logger(__name__)

def load_interim_records() -> pd.DataFrame:
    """
    Loads the pre-processed records from the interim directory.
    Expects data from T014/T015 to be present in data/interim/filtered_records.csv
    or similar intermediate state. Since T014/T015 modify the dataset in place
    or produce a specific intermediate file, we look for the result of the
    previous steps.
    
    Based on the task dependencies, T014 produces filtered data and T015 produces
    metadata. We assume the pipeline produces a consolidated 'filtered_adress.csv'
    or we must read the raw data and apply logic.
    
    However, the task description says "Depends on T014, T015".
    T014: Filter records -> likely saves to data/interim/filtered_adress.csv
    T015: Metadata extraction -> likely updates the dataframe or saves to data/interim/metadata.json
    
    We will attempt to load the output of T014. If it doesn't exist, we assume
    the pipeline is sequential and we might need to re-run the logic or load raw.
    For this implementation, we assume T014 saves 'data/interim/filtered_adress.csv'.
    """
    input_path = get_path("data/interim/filtered_adress.csv")
    
    if not os.path.exists(input_path):
        # Fallback: Try to load raw and apply T014/T015 logic locally if files missing
        # But per constraints, we should rely on previous tasks. 
        # If T014 failed, this task fails.
        raise FileNotFoundError(
            f"Intermediate file not found: {input_path}. "
            "Ensure T014 (filter_records) has run successfully."
        )
    
    logger.info(f"Loading intermediate records from {input_path}")
    df = pd.read_csv(input_path)
    return df

def apply_t014_t015_logic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the final logic from T014 and T015 if not already fully applied.
    T014: Filtered null labels and short text.
    T015: Added cognitive status metadata.
    
    This function ensures the dataframe has the required columns for the final output:
    - participant_id
    - label (Cognitive Status: Control, MCI, AD)
    - text (Cleaned transcript)
    - source_file (optional)
    """
    required_cols = ['participant_id', 'label', 'text']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Intermediate data missing required columns: {missing_cols}")
    
    # Ensure types
    df['participant_id'] = df['participant_id'].astype(str)
    df['label'] = df['label'].astype(str)
    df['text'] = df['text'].astype(str)
    
    # Log counts
    logger.info(f"Total records after filtering: {len(df)}")
    logger.info(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df

def write_cleaned_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Writes the cleaned dataset to the specified CSV path.
    """
    ensure_dirs(output_path.parent)
    logger.info(f"Writing cleaned dataset to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Successfully wrote cleaned dataset.")

def generate_derivation_log(df: pd.DataFrame, output_path: Path) -> None:
    """
    Generates a derivation log documenting the creation of this dataset.
    """
    log_entry = {
        "task_id": "T016",
        "description": "Create Cleaned Dataset",
        "input_source": "data/interim/filtered_adress.csv",
        "output_file": str(output_path),
        "record_count": len(df),
        "label_distribution": df['label'].value_counts().to_dict(),
        "steps": [
            "Loaded filtered records from T014",
            "Validated required columns (participant_id, label, text)",
            "Ensured data types",
            "Saved to data/interim/cleaned_adress.csv"
        ]
    }
    
    log_path = output_path.parent / "cleaned_adress_derivation.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_entry, f, indent=2)
    logger.info(f"Derivation log saved to {log_path}")

def main():
    """
    Main entry point for T016.
    """
    setup_logger = get_logger(__name__)
    setup_logger.setLevel(logging.INFO)
    
    try:
        # 1. Load intermediate data
        df = load_interim_records()
        
        # 2. Apply logic (validation, type casting)
        df_clean = apply_t014_t015_logic(df)
        
        # 3. Define output path
        output_path = get_path("data/interim/cleaned_adress.csv")
        
        # 4. Write dataset
        write_cleaned_dataset(df_clean, output_path)
        
        # 5. Generate derivation log
        generate_derivation_log(df_clean, output_path)
        
        logger.info("T016 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during T016 execution: {e}")
        raise

if __name__ == "__main__":
    main()
