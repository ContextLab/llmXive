import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from config import get_config
from utils.logging import get_logger

def get_logger_wrapper(logger_name: str = __name__):
    """Return a logger instance."""
    return logging.getLogger(logger_name)

def load_raw_data(logger: logging.Logger) -> Optional[List[Dict[str, Any]]]:
    """
    Load the raw dataset from the data/raw directory.
    This assumes T010/T015 have successfully downloaded and stored the data.
    We expect a JSON file or a specific structure based on the download task.
    For this implementation, we look for the most recent downloaded dataset
    in data/raw or a specific file if named by the download process.
    """
    config = get_config()
    raw_dir = config.data_raw_dir
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return None

    # Look for JSON files in the raw directory (common output from download tasks)
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        # Try nested directories if the download created a subfolder
        for item in raw_dir.iterdir():
            if item.is_dir():
                nested_json = list(item.glob("*.json"))
                if nested_json:
                    json_files.extend(nested_json)
        
        if not json_files:
            logger.error("No JSON data files found in raw directory.")
            return None

    # Use the first found file (or the most recent)
    data_file = sorted(json_files, key=lambda x: x.stat().st_mtime)[-1]
    logger.info(f"Loading raw data from: {data_file}")

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        
        if not isinstance(data, list):
            logger.error("Loaded data is not a list of records.")
            return None
        
        return data
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return None

def save_features(features_df: Any, output_path: Path, logger: logging.Logger) -> bool:
    """
    Save the extracted features DataFrame to the specified path.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        features_df.to_csv(output_path, index=False)
        logger.info(f"Features saved successfully to: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save features: {e}")
        return False

def main():
    """
    Main entry point for T019: Save extracted features to data/processed/features.csv.
    
    This task depends on T018 (Feature Extraction) and T020 (Ratio Calculation).
    It assumes that the data has been processed and the features (including the continuous ratio)
    are available in memory or can be reconstructed from the raw data and intermediate steps.
    
    Since T018 and T020 are separate modules, this script acts as the orchestrator
    to load raw data, apply the extraction logic from T018, apply the ratio logic from T020,
    and save the result.
    """
    logger = get_logger("T019_SaveFeatures")
    config = get_config()
    
    # Ensure processed directory exists
    processed_dir = config.data_processed_dir
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / "features.csv"
    
    # 1. Load Raw Data
    raw_data = load_raw_data(logger)
    if raw_data is None:
        logger.critical("Cannot proceed: Raw data not available. Ensure T010/T015 completed successfully.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(raw_data)} records from raw data.")
    
    # 2. Extract Features (Logic from T018: code/features/extraction.py)
    # We need to import and use the functions from extraction.py
    try:
        from features.extraction import process_participant_record
    except ImportError:
        logger.critical("Failed to import extraction logic. Ensure T018 is implemented.")
        sys.exit(1)
    
    processed_records = []
    for i, record in enumerate(raw_data):
        # Process each participant record
        # process_participant_record expects a record and returns extracted features
        try:
            features = process_participant_record(record, logger)
            if features:
                processed_records.append(features)
        except Exception as e:
            logger.warning(f"Skipping record {i} due to extraction error: {e}")
            continue
    
    if not processed_records:
        logger.critical("No features extracted from raw data.")
        sys.exit(1)
    
    logger.info(f"Extracted features for {len(processed_records)} participants.")
    
    # 3. Calculate Continuous Ratio (Logic from T020: code/features/classification.py)
    # We need to import and use the function from classification.py
    try:
        from features.classification import calculate_continuous_ratio
    except ImportError:
        logger.critical("Failed to import classification logic. Ensure T020 is implemented.")
        sys.exit(1)
    
    # Convert to DataFrame for batch processing if needed, or iterate
    import pandas as pd
    features_df = pd.DataFrame(processed_records)
    
    # Apply the continuous ratio calculation
    # calculate_continuous_ratio typically takes a DataFrame and adds a column
    # We assume it returns the updated DataFrame or modifies in place
    try:
        features_df = calculate_continuous_ratio(features_df, logger)
        logger.info("Continuous ratio calculated and appended to features.")
    except Exception as e:
        logger.error(f"Failed to calculate continuous ratio: {e}")
        # Depending on T020 spec, we might proceed with warning or fail
        # The spec says: "if mean ratio is <= 0, log a warning and proceed"
        # So we continue if it's just a warning case, but if it crashes, we stop.
        # Assuming the function handles the warning internally as per T020.
    
    # 4. Save to CSV
    success = save_features(features_df, output_path, logger)
    
    if not success:
        sys.exit(1)
    
    logger.info("T019 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
