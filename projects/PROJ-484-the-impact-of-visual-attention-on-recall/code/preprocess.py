import os
import sys
import json
import logging
import math
import argparse
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime

# Import logging configuration
from logging_config import setup_logging

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_LOGS_DIR = PROJECT_ROOT / "artifacts" / "logs"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-visual-attention-recall" / "contracts" / "dataset.schema.yaml"

# Ensure output directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = None

def setup_logger():
    global logger
    logger = setup_logging("preprocessing", str(ARTIFACTS_LOGS_DIR / "preprocessing.log"))
    return logger

def load_manifest(manifest_path):
    """Load the dataset manifest file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    with open(manifest_path, 'r') as f:
        return json.load(f)

def validate_variables(manifest, required_vars):
    """Check if required variables are present in the manifest."""
    missing = []
    for var in required_vars:
        if var not in manifest.get('variables', {}):
            missing.append(var)
    if missing:
        raise ValueError(f"Missing required variables in manifest: {missing}")
    return True

def extract_geometry_metadata(manifest):
    """Extract screen width, viewing distance, and sampling rate."""
    geo = manifest.get('geometry', {})
    required_geo = ['screen_width_pixels', 'viewing_distance_mm', 'sampling_rate_hz']
    missing = [k for k in required_geo if k not in geo]
    if missing:
        raise ValueError(f"Missing geometry metadata: {missing}")
    return geo

def calculate_ivt_threshold(geo, min_fixation_ms=100):
    """Calculate I-VT velocity threshold based on geometry."""
    # Simplified calculation: velocity = distance / time
    # Assume a saccade of 1 degree visual angle
    # 1 degree at distance D (mm) = 2 * D * tan(0.5 * deg) mm
    viewing_dist_mm = geo['viewing_distance_mm']
    deg_to_rad = math.pi / 180.0
    saccade_dist_mm = 2 * viewing_dist_mm * math.tan(0.5 * deg_to_rad)
    saccade_time_sec = min_fixation_ms / 1000.0
    velocity_mm_per_sec = saccade_dist_mm / saccade_time_sec
    # Convert to pixels per second (assuming screen width corresponds to FOV)
    # This is a heuristic; real implementation would use screen FOV calibration
    screen_width = geo['screen_width_pixels']
    # Assume 60 degrees horizontal FOV for estimation
    fov_deg = 60
    pixels_per_degree = screen_width / fov_deg
    velocity_pixels_per_sec = velocity_mm_per_sec * (pixels_per_degree / (viewing_dist_mm * math.tan(0.5 * deg_to_rad)))
    return velocity_pixels_per_sec

def extract_fixations_ivt(data, threshold, min_duration_ms=100):
    """
    Extract fixations using I-VT algorithm.
    data: DataFrame with 'x', 'y', 'timestamp' columns
    threshold: velocity threshold in pixels/sec
    min_duration_ms: minimum fixation duration in ms
    """
    if data.empty:
        return pd.DataFrame()

    # Sort by timestamp
    data = data.sort_values('timestamp').reset_index(drop=True)

    fixations = []
    current_fix = None
    sample_rate = 1000  # Assume 1000 Hz if not provided, or derive from data

    for i in range(len(data)):
        row = data.iloc[i]
        if i == 0:
            current_fix = {
                'start_idx': i,
                'end_idx': i,
                'start_time': row['timestamp'],
                'end_time': row['timestamp'],
                'points': [row]
            }
            continue

        prev_row = data.iloc[i-1]
        dt_ms = row['timestamp'] - prev_row['timestamp']
        if dt_ms <= 0:
            dt_ms = 1  # Avoid division by zero

        # Calculate velocity
        dx = row['x'] - prev_row['x']
        dy = row['y'] - prev_row['y']
        distance = math.sqrt(dx*dx + dy*dy)
        velocity = distance / (dt_ms / 1000.0)  # pixels per second

        if velocity < threshold:
            # Still in fixation
            current_fix['end_idx'] = i
            current_fix['end_time'] = row['timestamp']
            current_fix['points'].append(row)
        else:
            # Saccade detected, end current fixation if valid
            duration_ms = current_fix['end_time'] - current_fix['start_time']
            if duration_ms >= min_duration_ms:
                fixations.append(current_fix)
            # Start new fixation
            current_fix = {
                'start_idx': i,
                'end_idx': i,
                'start_time': row['timestamp'],
                'end_time': row['timestamp'],
                'points': [row]
            }

    # Don't forget the last fixation
    if current_fix:
        duration_ms = current_fix['end_time'] - current_fix['start_time']
        if duration_ms >= min_duration_ms:
            fixations.append(current_fix)

    # Convert to DataFrame
    if not fixations:
        return pd.DataFrame()

    result = []
    for f in fixations:
        result.append({
            'participant_id': f['points'][0].get('participant_id', ''),
            'trial_id': f['points'][0].get('trial_id', ''),
            'fixation_start': f['start_time'],
            'fixation_end': f['end_time'],
            'duration_ms': f['end_time'] - f['start_time'],
            'center_x': sum(p['x'] for p in f['points']) / len(f['points']),
            'center_y': sum(p['y'] for p in f['points']) / len(f['points'])
        })
    return pd.DataFrame(result)

def map_stimulus_valence(data, stimulus_map):
    """Map stimulus IDs to valence values."""
    if not stimulus_map:
        raise ValueError("Stimulus map is empty")

    # Assume data has 'stimulus_id' column
    if 'stimulus_id' not in data.columns:
        raise KeyError("stimulus_id column not found in data")

    # Map valence
    data['valence'] = data['stimulus_id'].map(stimulus_map)
    unmapped = data[data['valence'].isnull()]
    if not unmapped.empty:
        raise KeyError(f"Unmapped stimulus IDs found: {unmapped['stimulus_id'].unique()}")
    return data

def merge_stai_scores(data, stai_data):
    """Merge STAI scores with trial data."""
    if stai_data is None or stai_data.empty:
        logger.warning("STAI data is empty, proceeding without trait anxiety scores.")
        data['trait_anxiety'] = 0  # Default or handle appropriately
        return data

    # Assume stai_data has 'participant_id' and 'STAI_score'
    if 'participant_id' not in stai_data.columns or 'STAI_score' not in stai_data.columns:
        raise KeyError("STAI data missing required columns")

    data = data.merge(stai_data[['participant_id', 'STAI_score']], on='participant_id', how='left')
    data.rename(columns={'STAI_score': 'trait_anxiety'}, inplace=True)

    missing_stai = data[data['trait_anxiety'].isnull()]
    if not missing_stai.empty:
        logger.warning(f"Excluding {len(missing_stai)} trials for participants missing STAI scores.")
        data = data.dropna(subset=['trait_anxiety'])

    return data

def filter_trials(data, max_missing_pct=0.5, blink_threshold_ms=200):
    """Filter trials with excessive missing data or blinks."""
    if data.empty:
        return data

    # Filter by missing data (assuming 'missing_frames' column exists or calculate)
    # Here we assume data has a 'missing_frames' and 'total_frames' column
    if 'missing_frames' in data.columns and 'total_frames' in data.columns:
        data['missing_pct'] = data['missing_frames'] / data['total_frames']
        data = data[data['missing_pct'] <= max_missing_pct]

    # Filter by blink duration (assuming 'blink_duration_ms' column exists)
    if 'blink_duration_ms' in data.columns:
        data = data[data['blink_duration_ms'] <= blink_threshold_ms]

    return data.reset_index(drop=True)

def load_schema(schema_path):
    """Load the dataset schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(df, schema):
    """Validate DataFrame against the schema definition."""
    required_columns = schema.get('required_columns', [])
    column_types = schema.get('column_types', {})

    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == 'numeric' and not pd.api.types.is_numeric_dtype(df[col]):
                raise TypeError(f"Column {col} should be numeric")
            elif expected_type == 'string' and not pd.api.types.is_string_dtype(df[col]):
                raise TypeError(f"Column {col} should be string")

    # Check for nulls in required columns
    for col in required_columns:
        if df[col].isnull().any():
            raise ValueError(f"Column {col} contains null values")

    return True

def generate_analysis_csv(df, output_path):
    """Generate the final analysis-ready CSV with schema validation."""
    # Validate against schema
    schema = load_schema(SCHEMA_PATH)
    validate_against_schema(df, schema)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Analysis-ready CSV saved to: {output_path}")
    return True

def main():
    """Main entry point for preprocessing pipeline."""
    parser = argparse.ArgumentParser(description="Preprocess RSVP eye-tracking data")
    parser.add_argument('--manifest', type=str, required=True, help='Path to dataset manifest JSON')
    parser.add_argument('--eye-data', type=str, required=True, help='Path to eye-tracking data CSV')
    parser.add_argument('--stimuli', type=str, required=True, help='Path to stimulus mapping JSON')
    parser.add_argument('--stai', type=str, default=None, help='Path to STAI scores CSV')
    parser.add_argument('--output', type=str, default=str(DATA_PROCESSED_DIR / "analysis.csv"), help='Output CSV path')
    parser.add_argument('--min-fixation-ms', type=int, default=100, help='Minimum fixation duration in ms')
    args = parser.parse_args()

    setup_logger()
    logger.info("Starting preprocessing pipeline")

    # Load manifest
    manifest = load_manifest(args.manifest)
    logger.info("Manifest loaded")

    # Validate variables
    required_vars = ['eye_tracking', 'valence', 'recall', 'STAI']
    validate_variables(manifest, required_vars)
    logger.info("Variables validated")

    # Extract geometry
    geo = extract_geometry_metadata(manifest)
    threshold = calculate_ivt_threshold(geo, args.min_fixation_ms)
    logger.info(f"I-VT threshold calculated: {threshold:.2f} px/sec")

    # Load eye data
    eye_data = pd.read_csv(args.eye_data)
    logger.info(f"Loaded eye data: {len(eye_data)} rows")

    # Extract fixations
    fixations = extract_fixations_ivt(eye_data, threshold, args.min_fixation_ms)
    logger.info(f"Extracted {len(fixations)} fixations")

    # Load stimulus mapping
    with open(args.stimuli, 'r') as f:
        stimulus_map = json.load(f)

    # Map valence
    fixations = map_stimulus_valence(fixations, stimulus_map)
    logger.info("Stimulus valence mapped")

    # Load and merge STAI
    stai_data = None
    if args.stai and os.path.exists(args.stai):
        stai_data = pd.read_csv(args.stai)
    fixations = merge_stai_scores(fixations, stai_data)
    logger.info("STAI scores merged")

    # Filter trials
    fixations = filter_trials(fixations)
    logger.info(f"Trials filtered. Final count: {len(fixations)}")

    # Generate output
    generate_analysis_csv(fixations, args.output)
    logger.info("Preprocessing pipeline completed successfully")

if __name__ == "__main__":
    main()