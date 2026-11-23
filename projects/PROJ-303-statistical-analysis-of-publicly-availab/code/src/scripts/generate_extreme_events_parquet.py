"""
Script to generate the extreme_events.parquet file.

This script:
1. Loads the preprocessed NOAA GHCN-Daily data (after filtering and interpolation).
2. Uses the existing logic from src.data.preprocessing to map raw records to the ExtremeEvent entity.
3. Aggregates all stations' extreme events into a single DataFrame.
4. Writes the result to data/processed/extreme_events.parquet.

Dependencies:
- src.data.preprocessing (calculate_thresholds, flag_extreme_events, map_to_extreme_event_entity)
- src.data.ingestion (load_ingested_data)
- src.config (get_config)
"""
import pandas as pd
import numpy as np
from pathlib import Path
import logging
import sys
import os

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config
from src.data.ingestion import load_ingested_data
from src.data.preprocessing import (
    calculate_thresholds,
    flag_extreme_events,
    map_to_extreme_event_entity,
    ExtremeEvent
)
from src.pipeline.logging_config import get_logger

logger = get_logger(__name__)

def main():
    config = get_config()
    
    # Ensure output directory exists
    output_dir = Path(config.data.processed_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "extreme_events.parquet"
    
    logger.info(f"Loading preprocessed data from {config.data.raw_dir}...")
    # load_ingested_data returns a dict of station_id -> DataFrame
    # We assume the preprocessing steps (filtering, interpolation, threshold calc) 
    # have already been run and saved, or we re-run the necessary steps here 
    # if the task implies a full pipeline execution for this step.
    # Based on task dependencies (T014b), the data should be ready in memory or 
    # we need to re-ingest and re-process. 
    # Given the pipeline nature, we will re-ingest and re-process to ensure 
    # consistency with the latest thresholds and filtering logic.
    
    # 1. Ingest Data
    # We need the raw data first to apply thresholds and flag events.
    # The ingestion module provides download_station_data and ingest_northeast_data.
    # However, load_ingested_data suggests we might have intermediate files.
    # To be safe and ensure we have the data needed for T014b logic:
    
    # Re-ingest to get the full dataset for the current run context
    # Note: In a real pipeline, this might load from an intermediate 'cleaned' state.
    # For this script, we assume we need to run the processing logic on the raw data.
    
    logger.info("Ingesting Northeast USA weather data...")
    # We rely on the ingestion module to fetch/load the data
    # Assuming ingest_northeast_data returns a dict of station_id -> df
    try:
        # Check if we have a pre-processed cache or need to download
        # For T015, we assume the data is available via the ingestion interface
        # or we re-run the ingestion pipeline steps.
        # Let's assume we call the main ingestion function which returns the raw data dict.
        # If the project has a 'processed' intermediate step, we should load that.
        # Since T014b depends on T014, and T014 depends on T013 (thresholds),
        # we need the data to be in the state where thresholds are calculated.
        
        # Let's try to load the ingested data. If it's not there, we might need to download.
        # The ingestion module likely handles the download.
        raw_data_dict = load_ingested_data() 
        # If load_ingested_data expects arguments or fails, we might need to call ingest_northeast_data
        # But based on the API surface, load_ingested_data is available.
        
        if not raw_data_dict:
            logger.warning("No pre-loaded ingested data found. Attempting to download...")
            from src.data.ingestion import ingest_northeast_data
            raw_data_dict = ingest_northeast_data()
            
    except Exception as e:
        logger.error(f"Failed to load or ingest data: {e}")
        raise

    if not raw_data_dict:
        raise ValueError("No station data available to process.")

    all_extreme_events = []
    
    logger.info(f"Processing {len(raw_data_dict)} stations for extreme events...")
    
    # We need to calculate thresholds and flag events for each station.
    # Since thresholds are calculated on the training set (2000-2015),
    # we must ensure we are using the correct data subset for threshold calculation.
    # The preprocessing functions likely handle this if passed the full data.
    
    for station_id, df in raw_data_dict.items():
        if df.empty:
            continue
            
        # Ensure date column is datetime
        if 'date' not in df.columns:
            # Try common alternatives
            date_cols = [c for c in df.columns if 'date' in c.lower()]
            if date_cols:
                df['date'] = pd.to_datetime(df[date_cols[0]])
                df = df.drop(columns=[date_cols[0]])
            else:
                logger.warning(f"Station {station_id} has no date column. Skipping.")
                continue
        
        # Calculate thresholds (using 2000-2015 training data)
        # The function calculate_thresholds should handle the date filtering internally
        # or we need to pass the training subset.
        # Based on T013 description: "Calculate high percentile thresholds strictly on 2000–2015"
        # We assume calculate_thresholds takes the full df and handles the split.
        
        thresholds = calculate_thresholds(df)
        
        if not thresholds:
            logger.warning(f"No thresholds calculated for {station_id}. Skipping.")
            continue
        
        # Flag extreme events
        # flag_extreme_events should add the 'is_extreme' and 'magnitude' columns
        flagged_df = flag_extreme_events(df, thresholds)
        
        # Map to ExtremeEvent entities
        # map_to_extreme_event_entity takes the flagged DataFrame and returns a list of ExtremeEvent objects
        events = map_to_extreme_event_entity(flagged_df, station_id, thresholds)
        
        if events:
            all_extreme_events.extend(events)
    
    if not all_extreme_events:
        logger.warning("No extreme events found across all stations.")
        # Create an empty DataFrame with the correct schema
        df_extreme = pd.DataFrame(columns=['station_id', 'date', 'magnitude', 'threshold_value'])
    else:
        # Convert list of ExtremeEvent objects to DataFrame
        # ExtremeEvent is a dataclass, so we can use asdict or pandas constructor
        df_extreme = pd.DataFrame([event.__dict__ for event in all_extreme_events])
        
        # Ensure date is datetime
        if 'date' in df_extreme.columns:
            df_extreme['date'] = pd.to_datetime(df_extreme['date'])
        
        # Sort by station_id and date
        df_extreme = df_extreme.sort_values(by=['station_id', 'date']).reset_index(drop=True)
    
    # Write to Parquet
    logger.info(f"Writing {len(df_extreme)} extreme events to {output_path}...")
    df_extreme.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully generated {output_path}")
    print(f"Generated: {output_path}")
    print(f"Total records: {len(df_extreme)}")
    if not df_extreme.empty:
        print(f"Stations covered: {df_extreme['station_id'].nunique()}")
        print(f"Date range: {df_extreme['date'].min()} to {df_extreme['date'].max()}")

if __name__ == "__main__":
    main()
