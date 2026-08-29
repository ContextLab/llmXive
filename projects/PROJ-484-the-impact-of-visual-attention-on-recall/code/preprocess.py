import os
import sys
import json
import logging
import math
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import from local modules as per API surface
from logging_config import JsonFormatter, setup_logging
from config import get_config, get_data_path, get_random_seed

# Constants
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Setup a logger with JSON formatting and optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(JsonFormatter())
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JsonFormatter())
            logger.addHandler(file_handler)
            
    return logger

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the dataset manifest (JSON) containing file paths and metadata."""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading manifest from {manifest_path}")
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        return manifest
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        raise

def validate_variables(df: pd.DataFrame, required_vars: List[str]) -> bool:
    """Validate that all required variables are present in the dataframe."""
    logger = logging.getLogger(__name__)
    missing = [v for v in required_vars if v not in df.columns]
    if missing:
        logger.error(f"Missing required variables: {missing}")
        return False
    return True

def extract_geometry_metadata(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Extract screen width, viewing distance, and sampling rate from manifest."""
    logger = logging.getLogger(__name__)
    geometry = {
        'screen_width_px': 1920,
        'viewing_distance_cm': 60,
        'sampling_rate_hz': 60
    }
    
    # Try to extract from manifest if available
    if 'geometry' in manifest:
        geo_data = manifest['geometry']
        if 'screen_width_px' in geo_data:
            geometry['screen_width_px'] = geo_data['screen_width_px']
        if 'viewing_distance_cm' in geo_data:
            geometry['viewing_distance_cm'] = geo_data['viewing_distance_cm']
        if 'sampling_rate_hz' in geo_data:
            geometry['sampling_rate_hz'] = geo_data['sampling_rate_hz']
    
    logger.info(f"Geometry metadata: {geometry}")
    return geometry

def calculate_ivt_threshold(geometry: Dict[str, Any], deg_per_sec: float = 30.0) -> float:
    """Calculate the pixel threshold for I-VT algorithm."""
    # Calculate pixels per degree
    # Assuming a standard 24-inch monitor at 60cm distance
    # Visual angle = 2 * arctan(screen_width / (2 * distance))
    # For simplicity, we use an approximation: 1 degree ≈ 100 pixels at 60cm for 1920px width
    pixels_per_degree = geometry['screen_width_px'] / (2 * math.atan(math.radians(30)) * geometry['viewing_distance_cm'])
    
    # I-VT threshold: velocity in pixels per frame
    # velocity = (deg/s) * (pixels/deg) / (frames/s)
    threshold = (deg_per_sec * pixels_per_degree) / geometry['sampling_rate_hz']
    
    return threshold

def extract_fixations_ivt(gaze_data: pd.DataFrame, threshold: float, min_duration_ms: int = 100) -> pd.DataFrame:
    """Extract fixations from gaze data using I-VT algorithm."""
    logger = logging.getLogger(__name__)
    
    if gaze_data.empty:
        logger.warning("Empty gaze data provided")
        return pd.DataFrame()
    
    # Calculate velocity between consecutive samples
    gaze_data = gaze_data.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate displacement and velocity
    gaze_data['dx'] = gaze_data['x'].diff()
    gaze_data['dy'] = gaze_data['y'].diff()
    gaze_data['velocity'] = np.sqrt(gaze_data['dx']**2 + gaze_data['dy']**2)
    
    # Identify fixations (velocity below threshold)
    gaze_data['is_fixation'] = gaze_data['velocity'] < threshold
    
    # Group consecutive fixations
    gaze_data['group'] = (gaze_data['is_fixation'] != gaze_data['is_fixation'].shift()).cumsum()
    
    fixations = []
    for group_id, group in gaze_data[gaze_data['is_fixation']].groupby('group'):
        if len(group) >= 1:
            duration_ms = (group['timestamp'].max() - group['timestamp'].min())
            if duration_ms >= min_duration_ms:
                fixation = {
                    'start_time': group['timestamp'].min(),
                    'end_time': group['timestamp'].max(),
                    'duration_ms': duration_ms,
                    'avg_x': group['x'].mean(),
                    'avg_y': group['y'].mean(),
                    'sample_count': len(group)
                }
                fixations.append(fixation)
    
    if not fixations:
        logger.warning("No fixations found meeting minimum duration criteria")
        return pd.DataFrame()
    
    return pd.DataFrame(fixations)

def map_stimulus_valence(stimulus_ids: List[str], valence_map: Dict[str, float]) -> List[float]:
    """Map stimulus IDs to valence scores. Raise KeyError for unmapped IDs."""
    logger = logging.getLogger(__name__)
    mapped_vals = []
    unmapped = []
    
    for sid in stimulus_ids:
        if sid in valence_map:
            mapped_vals.append(valence_map[sid])
        else:
            unmapped.append(sid)
            mapped_vals.append(None)
    
    if unmapped:
        logger.warning(f"Unmapped stimulus IDs: {unmapped[:10]}... (total {len(unmapped)})")
        raise KeyError(f"Unmapped stimulus IDs found: {unmapped[:5]}")
    
    return mapped_vals

def merge_stai_scores(trials_df: pd.DataFrame, participants_df: pd.DataFrame) -> pd.DataFrame:
    """Merge STAI scores with trial data and filter participants without scores."""
    logger = logging.getLogger(__name__)
    
    # Ensure we have participant IDs in both
    if 'participant_id' not in trials_df.columns or 'participant_id' not in participants_df.columns:
        logger.error("participant_id column missing in one of the dataframes")
        raise ValueError("participant_id column missing")
    
    # Filter participants without STAI scores
    valid_participants = participants_df[participants_df['STAI_score'].notna()]
    logger.info(f"Participants with STAI scores: {len(valid_participants)} / {len(participants_df)}")
    
    # Merge
    merged = trials_df.merge(
        valid_participants[['participant_id', 'STAI_score']],
        on='participant_id',
        how='inner'
    )
    
    logger.info(f"Trials after filtering missing STAI: {len(merged)}")
    return merged

def filter_trials(df: pd.DataFrame, max_missing_pct: float = 0.5, max_blink_pct: float = 0.3) -> pd.DataFrame:
    """Filter trials based on missing data and blink duration."""
    logger = logging.getLogger(__name__)
    initial_count = len(df)
    
    # Filter trials with >50% missing frames
    if 'missing_frames_pct' in df.columns:
        df = df[df['missing_frames_pct'] <= max_missing_pct]
    
    # Filter trials with excessive blinks
    if 'blink_duration_pct' in df.columns:
        df = df[df['blink_duration_pct'] <= max_blink_pct]
    
    # Filter trials with missing critical data
    critical_cols = ['fixation_duration', 'valence', 'recall', 'STAI_score']
    for col in critical_cols:
        if col in df.columns:
            df = df[df[col].notna()]
    
    final_count = len(df)
    logger.info(f"Trials filtered: {initial_count} -> {final_count}")
    return df

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the dataset schema from YAML file."""
    logger = logging.getLogger(__name__)
    try:
        import yaml
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        return schema
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        raise

def validate_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate dataframe against the schema."""
    logger = logging.getLogger(__name__)
    is_valid = True
    
    # Check required columns
    required_cols = schema.get('required_columns', [])
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            is_valid = False
    
    # Check data types
    if 'column_types' in schema:
        for col, dtype in schema['column_types'].items():
            if col in df.columns:
                if dtype == 'numeric' and not pd.api.types.is_numeric_dtype(df[col]):
                    logger.error(f"Column {col} should be numeric")
                    is_valid = False
                elif dtype == 'string' and not pd.api.types.is_string_dtype(df[col]):
                    logger.error(f"Column {col} should be string")
                    is_valid = False
    
    # Check for nulls in required columns
    for col in required_cols:
        if col in df.columns and df[col].isnull().any():
            logger.error(f"Column {col} contains null values")
            is_valid = False
    
    if is_valid:
        logger.info("Schema validation passed")
    else:
        logger.error("Schema validation failed")
    
    return is_valid

def generate_analysis_csv(
    trials_df: pd.DataFrame,
    output_path: str,
    schema_path: str
) -> pd.DataFrame:
    """Generate the final analysis-ready CSV with schema validation."""
    logger = logging.getLogger(__name__)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Validate against schema
    schema = load_schema(schema_path)
    if not validate_against_schema(trials_df, schema):
        raise ValueError("Data does not match schema")
    
    # Ensure row count > 0
    if len(trials_df) == 0:
        raise ValueError("No data to write to CSV")
    
    # Write to CSV
    trials_df.to_csv(output_path, index=False)
    logger.info(f"Generated analysis CSV with {len(trials_df)} rows at {output_path}")
    
    # Verify file exists and is readable
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Output file not created: {output_path}")
    
    return trials_df

def main():
    """Main entry point for preprocessing pipeline."""
    parser = argparse.ArgumentParser(description='Preprocessing pipeline for RSVP dataset')
    parser.add_argument('--config', type=str, default='code/.env', help='Path to config file')
    parser.add_argument('--manifest', type=str, help='Path to dataset manifest')
    parser.add_argument('--output', type=str, default='data/processed/analysis.csv', help='Output CSV path')
    parser.add_argument('--schema', type=str, default='specs/001-visual-attention-recall/contracts/dataset.schema.yaml', help='Schema path')
    args = parser.parse_args()
    
    # Setup logging
    log_file = 'artifacts/logs/preprocessing.log'
    logger = setup_logger('preprocess', log_file)
    
    try:
        # Load configuration
        config = get_config(args.config)
        logger.info("Configuration loaded successfully")
        
        # Load manifest
        manifest_path = args.manifest or os.path.join(get_data_path(), 'manifest.json')
        manifest = load_manifest(manifest_path)
        
        # Load raw data (simulated for this implementation as per task requirements)
        # In a real scenario, this would load from data/raw/
        logger.info("Loading raw data...")
        
        # Since we cannot access real data in this environment, we simulate the pipeline
        # using the downloaded data structure if available, or raise an error if not
        raw_data_path = os.path.join(get_data_path(), 'raw', 'ds001435', 'derivatives', 'preprocessed', 'combined_trials.csv')
        
        if not os.path.exists(raw_data_path):
            # Try alternative paths
            alt_paths = [
                os.path.join(get_data_path(), 'raw', 'combined_trials.csv'),
                os.path.join(get_data_path(), 'processed', 'combined_trials.csv'),
            ]
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    raw_data_path = alt_path
                    break
        
        if not os.path.exists(raw_data_path):
            logger.error(f"Raw data not found at {raw_data_path}. Ensure T011b completed successfully.")
            raise FileNotFoundError(f"Raw data not found: {raw_data_path}")
        
        trials_df = pd.read_csv(raw_data_path)
        logger.info(f"Loaded {len(trials_df)} trials from {raw_data_path}")
        
        # Load participants data
        participants_path = os.path.join(get_data_path(), 'raw', 'participants.tsv')
        if not os.path.exists(participants_path):
            # Try alternative
            participants_path = os.path.join(get_data_path(), 'raw', 'ds001435', 'participants.tsv')
        
        if os.path.exists(participants_path):
            participants_df = pd.read_csv(participants_path, sep='\t')
            trials_df = merge_stai_scores(trials_df, participants_df)
        else:
            logger.warning("Participants file not found, skipping STAI merge")
        
        # Filter trials
        trials_df = filter_trials(trials_df)
        
        # Generate final CSV
        output_df = generate_analysis_csv(trials_df, args.output, args.schema)
        
        logger.info("Preprocessing pipeline completed successfully")
        print(f"Analysis CSV generated: {args.output} ({len(output_df)} rows)")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()