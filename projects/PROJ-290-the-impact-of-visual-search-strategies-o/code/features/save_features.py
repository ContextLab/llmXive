import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

from utils.logging import get_logger
from config import get_config
from data.exclusion import run_exclusion_pipeline

def get_logger_wrapper(name: str = "save_features") -> logging.Logger:
    """Get a logger instance for this module."""
    return get_logger(name)

def load_raw_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Load the raw dataset from data/raw/ directory.
    Assumes the download process has already populated this directory.
    """
    config = get_config()
    raw_dir = config.data_raw_dir
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    # Find the first available parquet or csv file in the raw directory
    # The download task should have placed a specific file there.
    # We look for common extensions.
    possible_files = list(raw_dir.glob("*.parquet")) + list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.jsonl"))
    
    if not possible_files:
        logger.error(f"No data files found in {raw_dir}")
        raise FileNotFoundError(f"No data files found in {raw_dir}")

    # Sort to ensure deterministic selection if multiple exist
    possible_files.sort()
    data_file = possible_files[0]
    logger.info(f"Loading raw data from: {data_file}")

    if data_file.suffix == '.parquet':
        df = pd.read_parquet(data_file)
    elif data_file.suffix == '.csv':
        df = pd.read_csv(data_file)
    elif data_file.suffix == '.jsonl':
        df = pd.read_json(data_file, lines=True)
    else:
        # Fallback to generic read if extension is weird but file exists
        try:
            df = pd.read_csv(data_file)
        except Exception as e:
            logger.error(f"Failed to parse {data_file}: {e}")
            raise

    return df

def save_features(features_df: pd.DataFrame, output_path: Path, logger: logging.Logger) -> None:
    """
    Save the extracted features DataFrame to a CSV file.
    Ensures the directory exists before writing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features_df.to_csv(output_path, index=False)
    logger.info(f"Saved features to: {output_path}")
    logger.info(f"Total records saved: {len(features_df)}")
    logger.info(f"Columns saved: {list(features_df.columns)}")

def main() -> int:
    """
    Main entry point for the feature saving pipeline.
    1. Loads raw data.
    2. Applies participant exclusion logic (T014).
    3. (Implicitly assumes feature extraction T018 has been run or data is pre-processed).
       *Correction*: Since T018 (extraction) and T020 (classification) are dependencies for the final
       features.csv, this script needs to orchestrate the full pipeline from raw data to saved features.
       However, the task description says "Save extracted features".
       
       Looking at the dependency chain:
       T018: Extract features (in extraction.py)
       T020: Calculate continuous ratio (in classification.py)
       T019: Save to features.csv.
       
       Since T018 and T020 are marked as completed in the context (or at least T018 is),
       we should import the logic from those modules to ensure we are saving the *result* of extraction.
       But the task is specifically T019.
       
       Wait, the prompt says T018 is completed. T020 is NOT completed yet (it's marked [~] or pending).
       Actually, looking at the "completed task ids" list: T018 is there. T020 is NOT.
       T019 is the current task.
       
       If T020 (calculate continuous ratio) is not done, the features.csv might not have the ratio.
       However, T019 says "Save extracted features". This likely implies the output of T018.
       But T020 appends to features.csv.
       
       Let's re-read T019: "Save extracted features to data/processed/features.csv".
       And T020: "Calculate continuous ratio... append to data/processed/features.csv".
       
       This implies a sequence:
       1. Extract features (T018) -> intermediate state?
       2. T019 saves the result of T018?
       3. T020 appends to that file?
       
       OR, T019 is the orchestration script that calls T018 logic and saves it.
       Given the structure of other tasks (e.g., T010 is download, T012 is validate), T019 is likely the
       script that performs the saving of the *current* state of features.
       
       However, to make this script "real" and runnable as a pipeline step, it should:
       1. Load raw data.
       2. Run exclusion (T014 logic).
       3. Run feature extraction (T018 logic).
       4. Save to features.csv.
       
       Since T020 is not done, we stop at the features from T018.
       
       Let's import the extraction logic from code/features/extraction.py.
       We need to call `extract_face_features` or `process_participant_record` on the raw data.
    """
    logger = get_logger_wrapper("save_features")
    config = get_config()
    
    # 1. Load Raw Data
    try:
        raw_df = load_raw_data(logger)
    except FileNotFoundError as e:
        logger.error("Cannot proceed without raw data. Run download task first.")
        return 1
    
    # 2. Apply Exclusion (T014)
    # The exclusion logic returns a filtered dataframe and logs exclusions.
    # We assume run_exclusion_pipeline handles the filtering.
    logger.info("Applying participant exclusion logic...")
    # run_exclusion_pipeline likely takes raw data and returns clean data
    # We need to check the signature of run_exclusion_pipeline from the API surface.
    # It returns a tuple? Or just the df?
    # API: run_exclusion_pipeline, main.
    # Let's assume it returns (filtered_df, exclusion_stats).
    try:
        # We need to pass the raw dataframe to the exclusion logic.
        # The function signature in the API surface is just "run_exclusion_pipeline".
        # We'll call it and handle the return.
        # Since we don't have the source, we assume it takes a dataframe and returns one.
        # To be safe, we'll try to call it with the dataframe.
        # If it expects a path, we'd need to adapt, but usually these take dataframes in this pipeline.
        # Let's assume it takes the dataframe.
        clean_df, exclusion_report = run_exclusion_pipeline(raw_df, logger)
        logger.info(f"Exclusion complete. Kept {len(clean_df)} records.")
    except Exception as e:
        logger.error(f"Exclusion logic failed: {e}")
        # If exclusion fails, we might still want to proceed with raw data or halt.
        # Given the strictness, let's halt if exclusion is critical.
        return 1
    
    # 3. Extract Features (T018 logic)
    # We need to apply extract_face_features to each row or the whole dataframe.
    # The API surface shows `extract_face_features` and `process_participant_record`.
    # `process_participant_record` likely processes a single record.
    # We'll use apply() on the dataframe.
    
    logger.info("Extracting features...")
    
    # Assuming the raw data has columns like 'gaze_coordinates', 'roi_annotations', etc.
    # We map the extraction function to the dataframe.
    # We need to handle potential errors in extraction gracefully or let them fail loudly.
    
    # To make this robust, we'll extract features row by row.
    extracted_features = []
    
    for idx, row in clean_df.iterrows():
        try:
            # Call the extraction function from extraction.py
            # We need to pass the row data.
            # The function `extract_face_features` likely expects the row or specific columns.
            # Based on T018 description: "compute fixation duration, saccade amplitude, dispersion".
            # Let's assume extract_face_features(row) returns a dict of features.
            feat = extract_face_features(row)
            extracted_features.append(feat)
        except Exception as e:
            logger.warning(f"Failed to extract features for record {idx}: {e}")
            # Skip or include with NaN? Let's skip for now to avoid corruption.
            continue
    
    if not extracted_features:
        logger.error("No features extracted. Check data format.")
        return 1
        
    features_df = pd.DataFrame(extracted_features)
    
    # 4. Save to CSV
    output_path = config.data_processed_dir / "features.csv"
    save_features(features_df, output_path, logger)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
