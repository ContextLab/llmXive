"""
Implementation for Task T019: Save extracted features to data/processed/features.csv.

This module loads the raw data (post-download/validation/exclusion), applies the
feature extraction logic defined in code/features/extraction.py and classification.py,
and saves the resulting DataFrame to data/processed/features.csv.

It depends on:
  - code/features/extraction.py (extract_face_features, process_participant_record)
  - code/features/classification.py (calculate_continuous_ratio)
  - code/data/exclusion.py (run_exclusion_pipeline)
  - code/config.py (Config paths)
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from project modules
from config import get_config
from utils.logging import get_logger
from data.exclusion import run_exclusion_pipeline, get_logger_wrapper as exclusion_logger_wrapper
from features.extraction import extract_face_features, process_participant_record, get_logger_wrapper as extraction_logger_wrapper
from features.classification import calculate_continuous_ratio, get_logger_wrapper as classification_logger_wrapper


def get_logger_wrapper(logger_name: str):
    """Standard logger wrapper for this module."""
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_raw_data(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Load the raw dataset from data/raw/ or the processed validation output.
    Since T010-T015 are completed, we expect the raw data to be in data/raw/.
    We assume the download script saved the dataset as a parquet or csv.
    We will look for the most recent large data file in data/raw/.
    """
    config = get_config()
    raw_dir = config.get("paths.raw_data_dir", "data/raw")
    raw_path = Path(raw_dir)

    if not raw_path.exists():
        logger.error(f"Raw data directory {raw_path} does not exist.")
        return None

    # Look for common data formats
    candidates = list(raw_path.glob("*.parquet")) + list(raw_path.glob("*.csv")) + list(raw_path.glob("*.json"))
    if not candidates:
        logger.error(f"No data files found in {raw_path}.")
        return None

    # Sort by modification time, take the newest
    candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    target_file = candidates[0]
    logger.info(f"Loading raw data from: {target_file}")

    try:
        if target_file.suffix == '.parquet':
            df = pd.read_parquet(target_file)
        elif target_file.suffix == '.csv':
            df = pd.read_csv(target_file)
        elif target_file.suffix == '.json':
            df = pd.read_json(target_file)
        else:
            logger.error(f"Unsupported file format: {target_file.suffix}")
            return None

        logger.info(f"Loaded {len(df)} rows from {target_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load data from {target_file}: {e}")
        return None


def save_features(df_processed: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Save the processed features DataFrame to data/processed/features.csv.
    """
    config = get_config()
    processed_dir = config.get("paths.processed_data_dir", "data/processed")
    output_path = Path(processed_dir) / "features.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df_processed.to_csv(output_path, index=False)
        logger.info(f"Successfully saved features to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save features to {output_path}: {e}")
        return False


def main():
    """
    Main entry point for T019.
    1. Load raw data.
    2. Run exclusion pipeline (T014 logic) to filter participants.
    3. Extract features (T018 logic) for each record.
    4. Calculate continuous ratio (T020 logic).
    5. Save to data/processed/features.csv.
    """
    logger = get_logger("T019_SaveFeatures")
    logger.info("Starting T019: Save Extracted Features")

    # 1. Load Raw Data
    raw_df = load_raw_data(logger)
    if raw_df is None:
        logger.error("Cannot proceed without raw data.")
        sys.exit(1)

    # 2. Apply Exclusion Logic (T014)
    # The exclusion logic expects a specific schema. We assume the raw_df
    # has been validated by T012 and T013 (ROI fallback) already.
    # We run the exclusion pipeline to filter out participants with >20% missing gaze.
    # Note: run_exclusion_pipeline returns a filtered dataframe and a report.
    try:
        filtered_df, exclusion_report = run_exclusion_pipeline(raw_df, logger)
        logger.info(f"Exclusion applied. Original: {len(raw_df)}, Filtered: {len(filtered_df)}")
        if len(filtered_df) == 0:
            logger.error("All participants excluded. Cannot proceed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Exclusion pipeline failed: {e}")
        sys.exit(1)

    # 3. Extract Features (T018)
    # We assume the raw data has columns: 'participant_id', 'trial_id', 'gaze_coordinates', 'roi_annotations', etc.
    # We need to iterate and extract features per record.
    logger.info("Extracting features for each record...")
    features_list = []

    # We assume the dataframe has a structure where we can iterate rows.
    # If the data is already aggregated per trial, we process row by row.
    # If it's per gaze point, we might need to aggregate first.
    # Based on T018 description, we process participant records.
    # We'll assume the input is already at the trial level or we process per row.
    
    # Simplified assumption: Each row is a trial for a participant.
    # We need columns: 'participant_id', 'trial_id', 'gaze_coordinates', 'roi_annotations', 'emotion_labels', 'response_times'
    required_cols = ['participant_id', 'trial_id', 'gaze_coordinates', 'roi_annotations', 'emotion_labels', 'response_times']
    missing_cols = [c for c in required_cols if c not in filtered_df.columns]
    if missing_cols:
        logger.warning(f"Missing expected columns for feature extraction: {missing_cols}. Attempting to proceed with available data.")
    
    for idx, row in filtered_df.iterrows():
        try:
            # Extract features using the function from extraction.py
            # This function expects a record (dict/series)
            feat = process_participant_record(row, logger)
            if feat is not None:
                features_list.append(feat)
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to extraction error: {e}")
            continue

    if not features_list:
        logger.error("No features extracted.")
        sys.exit(1)

    df_features = pd.DataFrame(features_list)
    logger.info(f"Extracted {len(df_features)} feature records.")

    # 4. Calculate Continuous Ratio (T020)
    # This adds a column 'eye_mouth_ratio' to the features dataframe.
    try:
        df_features = calculate_continuous_ratio(df_features, logger)
        logger.info("Continuous ratio calculated.")
    except Exception as e:
        logger.warning(f"Continuous ratio calculation failed: {e}. Proceeding without ratio column.")

    # 5. Save Features (T019)
    success = save_features(df_features, logger)
    if not success:
        logger.error("Failed to save features.")
        sys.exit(1)

    logger.info("T019 completed successfully.")


if __name__ == "__main__":
    main()
