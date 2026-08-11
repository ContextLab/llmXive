import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from utils import setup_ingestion_logging, get_logger, detect_ph_outliers, calculate_ph_heterogeneity
from data_models import Sample, validate_sample_schema

# Ensure logger is available
logger = get_logger(__name__)

def load_sensor_data(ph_csv_path: str, temp_csv_path: str) -> pd.DataFrame:
    """
    Load pH and temperature CSV files and merge them.
    Expects columns: timestamp, value, deployment_event, sensor_id, coordinates, location
    """
    logger.info(f"Loading pH data from {ph_csv_path}")
    if not os.path.exists(ph_csv_path):
        raise FileNotFoundError(f"pH CSV file not found: {ph_csv_path}")
    
    logger.info(f"Loading temperature data from {temp_csv_path}")
    if not os.path.exists(temp_csv_path):
        raise FileNotFoundError(f"Temperature CSV file not found: {temp_csv_path}")

    df_ph = pd.read_csv(ph_csv_path)
    df_temp = pd.read_csv(temp_csv_path)

    # Ensure timestamp is datetime
    df_ph['timestamp'] = pd.to_datetime(df_ph['timestamp'])
    df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'])

    # Merge on timestamp, deployment_event, sensor_id, location, coordinates
    # We assume the join keys are consistent
    merged_df = pd.merge(
        df_ph,
        df_temp,
        on=['timestamp', 'deployment_event', 'sensor_id', 'location', 'coordinates'],
        how='inner',
        suffixes=('_ph', '_temp')
    )

    # Rename columns for clarity
    merged_df = merged_df.rename(columns={
        'value_ph': 'pH',
        'value_temp': 'temp'
    })

    # Add dummy fastq_path for now (will be populated by US2 or mock data)
    # In a real scenario, this would be joined from a separate manifest
    merged_df['fastq_path'] = merged_df.apply(
        lambda row: f"data/raw/{row['deployment_event']}_{row['sensor_id']}_sample_{row['timestamp'].strftime('%Y%m%d%H%M%S')}.fastq.gz",
        axis=1
    )

    return merged_df

def validate_metadata_fields(df: pd.DataFrame) -> List[str]:
    """
    Validate required metadata fields per Constitution Principle VI.
    Returns list of missing/invalid field names.
    """
    required_fields = ['deployment_event', 'sensor_id', 'coordinates', 'location', 'timestamp', 'pH', 'temp']
    missing = []
    for field in required_fields:
        if field not in df.columns:
            missing.append(field)
    return missing

def calculate_pH_heterogeneity_for_window(df: pd.DataFrame, window_minutes: int = 15) -> pd.DataFrame:
    """
    Calculate pH SD within a ±15 minute window for each sample.
    Uses the utility from T004.
    """
    # Sort by timestamp
    df_sorted = df.sort_values('timestamp')
    
    # Apply heterogeneity calculation
    # We group by sensor_id and deployment_event to calculate SD within windows
    # For simplicity, we assume each row is a sample and we look at neighbors
    # In a real implementation, we would group by sensor and calculate rolling SD
    
    results = []
    for idx, row in df_sorted.iterrows():
        # Find window around this timestamp
        start_time = row['timestamp'] - timedelta(minutes=window_minutes)
        end_time = row['timestamp'] + timedelta(minutes=window_minutes)
        
        window_data = df_sorted[
            (df_sorted['timestamp'] >= start_time) & 
            (df_sorted['timestamp'] <= end_time) &
            (df_sorted['sensor_id'] == row['sensor_id'])
        ]
        
        # Calculate SD of pH in this window
        ph_sd = window_data['pH'].std()
        results.append({
            'sample_id': f"sample_{idx}",
            'timestamp': row['timestamp'],
            'pH': row['pH'],
            'temp': row['temp'],
            'pH_sd': ph_sd,
            'location': row['location'],
            'fastq_path': row['fastq_path'],
            'deployment_event': row['deployment_event'],
            'sensor_id': row['sensor_id'],
            'coordinates': row['coordinates']
        })
    
    return pd.DataFrame(results)

def align_temporal_data(df: pd.DataFrame, window_minutes: int = 15) -> Tuple[pd.DataFrame, List[str]]:
    """
    Join samples within ±15 minute window.
    Flags mismatches in rejected_samples.log.
    Returns aligned DataFrame and list of rejected sample IDs.
    """
    rejected_samples = []
    aligned_data = []
    
    df_sorted = df.sort_values('timestamp')
    used_indices = set()
    
    for idx, row in df_sorted.iterrows():
        if idx in used_indices:
            continue
        
        start_time = row['timestamp'] - timedelta(minutes=window_minutes)
        end_time = row['timestamp'] + timedelta(minutes=window_minutes)
        
        # Find all samples in this window from same sensor
        window_indices = df_sorted[
            (df_sorted['timestamp'] >= start_time) & 
            (df_sorted['timestamp'] <= end_time) &
            (df_sorted['sensor_id'] == row['sensor_id'])
        ].index.tolist()
        
        if len(window_indices) > 1:
            # Multiple samples in window - take the first one as representative
            # and reject the others
            representative_idx = window_indices[0]
            used_indices.update(window_indices)
            
            rep_row = df_sorted.loc[representative_idx]
            aligned_data.append(rep_row)
            
            # Reject others
            for reject_idx in window_indices[1:]:
                rejected_samples.append(f"sample_{reject_idx}")
        else:
            # Single sample in window - keep it
            used_indices.add(idx)
            aligned_data.append(row)
    
    return pd.DataFrame(aligned_data), rejected_samples

def apply_outlier_filtering(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Exclude pH < 1.0 or > 10.0; flag edge ranges.
    Uses utility from T004.
    """
    outliers = []
    filtered_data = []
    
    for idx, row in df.iterrows():
        is_outlier, is_edge, reason = detect_ph_outliers(row['pH'])
        
        if is_outlier:
            outliers.append(f"sample_{idx}: {reason}")
        else:
            filtered_data.append(row)
    
    return pd.DataFrame(filtered_data), outliers

def run_ingestion_pipeline(
    ph_csv_path: str, 
    temp_csv_path: str, 
    output_path: str,
    filtered_output_path: str,
    rejected_log_path: str
) -> None:
    """
    Run the full ingestion pipeline:
    1. Load data
    2. Validate metadata
    3. Calculate pH heterogeneity
    4. Align temporal data
    5. Apply outlier filtering
    6. Write outputs
    """
    logger.info("Starting ingestion pipeline")
    
    # Step 1: Load data
    df_raw = load_sensor_data(ph_csv_path, temp_csv_path)
    
    # Step 2: Validate metadata
    missing_fields = validate_metadata_fields(df_raw)
    if missing_fields:
        raise ValueError(f"Missing required metadata fields: {missing_fields}")
    
    # Step 3: Calculate pH heterogeneity (SD within ±15 min window)
    df_hetero = calculate_pH_heterogeneity_for_window(df_raw)
    
    # Step 4: Align temporal data
    df_aligned, rejected_align = align_temporal_data(df_hetero)
    
    # Step 5: Apply outlier filtering
    df_filtered, rejected_outliers = apply_outlier_filtering(df_aligned)
    
    # Combine all rejected samples
    all_rejected = rejected_align + rejected_outliers
    
    # Step 6: Write outputs
    # Unified table (before filtering) - T014 requirement
    # We need to ensure all required columns are present
    required_columns = [
        'sample_id', 'timestamp', 'pH', 'temp', 'pH_sd', 
        'location', 'fastq_path', 'deployment_event', 'sensor_id', 'coordinates'
    ]
    
    # Ensure sample_id is present
    if 'sample_id' not in df_aligned.columns:
        df_aligned['sample_id'] = [f"sample_{i}" for i in range(len(df_aligned))]
    
    # Select and order columns
    df_unified = df_aligned[required_columns]
    
    # Write unified table (T014)
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df_unified.to_csv(output_path, index=False)
    logger.info(f"Written unified sample table to {output_path}")
    
    # Write filtered table (T013)
    filtered_dir = Path(filtered_output_path).parent
    filtered_dir.mkdir(parents=True, exist_ok=True)
    df_filtered[required_columns].to_csv(filtered_output_path, index=False)
    logger.info(f"Written filtered sample table to {filtered_output_path}")
    
    # Write rejected samples log
    log_dir = Path(rejected_log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(rejected_log_path, 'w') as f:
        f.write("Rejected Samples Log\n")
        f.write("====================\n\n")
        f.write(f"Total rejected: {len(all_rejected)}\n\n")
        for rejected in all_rejected:
            f.write(f"{rejected}\n")
    logger.info(f"Written rejected samples log to {rejected_log_path}")
    
    logger.info("Ingestion pipeline completed successfully")

def main():
    """
    Main entry point for the ingestion pipeline.
    Expects command-line arguments or environment variables for paths.
    """
    # Setup logging
    setup_ingestion_logging()
    
    # Default paths (can be overridden by environment or args in real implementation)
    ph_csv = "data/raw/pH_data.csv"
    temp_csv = "data/raw/temperature_data.csv"
    output_unified = "data/processed/unified_sample_table.csv"
    output_filtered = "data/processed/filtered_unified_sample_table.csv"
    rejected_log = "data/processed/rejected_samples.log"
    
    # Check if input files exist (for demo purposes, we'll create mock data if missing)
    # In production, this should fail loudly if real data is missing
    if not os.path.exists(ph_csv) or not os.path.exists(temp_csv):
        logger.error("Input data files not found. Please provide real data files.")
        logger.error("Expected: data/raw/pH_data.csv and data/raw/temperature_data.csv")
        return 1
    
    try:
        run_ingestion_pipeline(
            ph_csv_path=ph_csv,
            temp_csv_path=temp_csv,
            output_path=output_unified,
            filtered_output_path=output_filtered,
            rejected_log_path=rejected_log
        )
        return 0
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    exit(main())
