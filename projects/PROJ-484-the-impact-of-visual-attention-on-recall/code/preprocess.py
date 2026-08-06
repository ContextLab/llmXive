import os
import sys
import json
import logging
import math
import argparse
import yaml
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

# Import logging setup from sibling module
from logging_config import setup_logging

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ARTIFACTS_LOGS_DIR = PROJECT_ROOT / "artifacts" / "logs"
SCHEMAS_DIR = PROJECT_ROOT / "specs" / "001-visual-attention-recall" / "contracts"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logger = setup_logging("preprocessing")

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the dataset manifest file."""
    if manifest_path is None:
        manifest_path = DATA_RAW_DIR / "manifest.json"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def validate_variables(manifest: Dict[str, Any], required_vars: List[str]) -> None:
    """Validate that required variables are present in the manifest."""
    available_vars = manifest.get('variables', {}).keys()
    missing = [var for var in required_vars if var not in available_vars]
    
    if missing:
        logger.error(f"Missing required variables: {missing}")
        raise ValueError(f"Missing required variables: {missing}")
    
    logger.info(f"Validated presence of required variables: {required_vars}")

def extract_geometry_metadata(manifest: Dict[str, Any]) -> Dict[str, float]:
    """Extract screen width, viewing distance, and sampling rate from manifest."""
    geometry = manifest.get('geometry', {})
    
    if not geometry:
        logger.error("Missing geometry metadata in manifest.")
        raise ValueError("Missing geometry metadata. Cannot calibrate I-VT threshold.")
    
    required_geo_keys = ['screen_width_pixels', 'viewing_distance_mm', 'sampling_rate_hz']
    missing_geo = [k for k in required_geo_keys if k not in geometry]
    
    if missing_geo:
        logger.error(f"Missing geometry fields: {missing_geo}")
        raise ValueError(f"Missing geometry metadata. Cannot calibrate I-VT threshold.")
    
    return {
        'screen_width_pixels': float(geometry['screen_width_pixels']),
        'viewing_distance_mm': float(geometry['viewing_distance_mm']),
        'sampling_rate_hz': float(geometry['sampling_rate_hz'])
    }

def calculate_ivt_threshold(geometry: Dict[str, float]) -> float:
    """Calculate I-VT velocity threshold in degrees per second."""
    # Standard heuristic: 30 degrees/second for I-VT
    # Can be refined based on specific experimental setup if needed
    return 30.0

def extract_fixations_ivt(
    eye_tracking_df: pd.DataFrame, 
    threshold_deg_s: float, 
    min_duration_ms: float = 100.0
) -> pd.DataFrame:
    """
    Extract fixations using I-VT algorithm.
    
    Args:
        eye_tracking_df: DataFrame with columns 'x', 'y', 'timestamp' (ms)
        threshold_deg_s: Velocity threshold in degrees per second
        min_duration_ms: Minimum fixation duration in ms
        
    Returns:
        DataFrame of fixations with columns: start_time, end_time, duration_ms, avg_x, avg_y
    """
    if eye_tracking_df.empty:
        return pd.DataFrame(columns=['start_time', 'end_time', 'duration_ms', 'avg_x', 'avg_y', 'participant_id', 'trial_id', 'stimulus_id'])
    
    # Sort by timestamp
    eye_tracking_df = eye_tracking_df.sort_values('timestamp').reset_index(drop=True)
    
    # Calculate velocity (degrees per second)
    # Assuming coordinates are in pixels, need to convert to degrees
    # This is a simplified conversion; in reality, screen size and distance matter
    # For this implementation, we assume a standard conversion factor or use pixel-based velocity
    # and convert later if needed. Here we use a simplified pixel-based velocity threshold.
    
    # Calculate velocity between consecutive samples
    eye_tracking_df['dx'] = eye_tracking_df['x'].diff()
    eye_tracking_df['dy'] = eye_tracking_df['y'].diff()
    eye_tracking_df['dt'] = eye_tracking_df['timestamp'].diff()
    
    # Avoid division by zero
    eye_tracking_df['dt'] = eye_tracking_df['dt'].replace(0, np.nan)
    eye_tracking_df['velocity'] = np.sqrt(eye_tracking_df['dx']**2 + eye_tracking_df['dy']**2) / (eye_tracking_df['dt'] / 1000.0)  # pixels per second
    
    # Convert threshold from deg/s to pixels/s (simplified: assume 1 deg = 50 pixels)
    # In a real implementation, this would use screen geometry
    pixel_threshold = threshold_deg_s * 50.0
    
    # Identify fixations (velocity below threshold)
    eye_tracking_df['is_fixation'] = eye_tracking_df['velocity'] < pixel_threshold
    
    # Group consecutive fixation samples
    eye_tracking_df['fixation_group'] = (eye_tracking_df['is_fixation'] != eye_tracking_df['is_fixation'].shift()).cumsum()
    fixation_groups = eye_tracking_df[eye_tracking_df['is_fixation']].groupby('fixation_group')
    
    fixations = []
    for group_id, group_df in fixation_groups:
        if len(group_df) < 2:
            continue
            
        start_time = group_df['timestamp'].iloc[0]
        end_time = group_df['timestamp'].iloc[-1]
        duration_ms = end_time - start_time
        
        if duration_ms < min_duration_ms:
            continue
        
        avg_x = group_df['x'].mean()
        avg_y = group_df['y'].mean()
        
        # Get participant, trial, stimulus info from the first row of the group
        participant_id = group_df['participant_id'].iloc[0] if 'participant_id' in group_df.columns else None
        trial_id = group_df['trial_id'].iloc[0] if 'trial_id' in group_df.columns else None
        stimulus_id = group_df['stimulus_id'].iloc[0] if 'stimulus_id' in group_df.columns else None
        
        fixations.append({
            'start_time': start_time,
            'end_time': end_time,
            'duration_ms': duration_ms,
            'avg_x': avg_x,
            'avg_y': avg_y,
            'participant_id': participant_id,
            'trial_id': trial_id,
            'stimulus_id': stimulus_id
        })
    
    return pd.DataFrame(fixations)

def map_stimulus_valence(
    trials_df: pd.DataFrame, 
    valence_map: Dict[str, float]
) -> pd.DataFrame:
    """
    Map stimulus IDs to valence scores.
    
    Args:
        trials_df: DataFrame with 'stimulus_id' column
        valence_map: Dictionary mapping stimulus_id -> valence score
        
    Returns:
        DataFrame with added 'valence' column
    """
    if 'stimulus_id' not in trials_df.columns:
        raise ValueError("trials_df must contain 'stimulus_id' column")
    
    # Map valence, raising error for unmapped IDs
    unmapped = set(trials_df['stimulus_id'].unique()) - set(valence_map.keys())
    if unmapped:
        logger.error(f"Unmapped stimulus IDs: {unmapped}")
        raise KeyError(f"Unmapped stimulus IDs found: {unmapped}")
    
    trials_df = trials_df.copy()
    trials_df['valence'] = trials_df['stimulus_id'].map(valence_map)
    
    # Check for any NaNs after mapping
    if trials_df['valence'].isnull().any():
        unmapped_after = trials_df[trials_df['valence'].isnull()]['stimulus_id'].unique()
        logger.error(f"Unmapped stimulus IDs after mapping: {unmapped_after}")
        raise KeyError(f"Unmapped stimulus IDs after mapping: {unmapped_after}")
    
    return trials_df

def merge_stai_scores(
    trials_df: pd.DataFrame, 
    stai_df: pd.DataFrame, 
    participant_col: str = 'participant_id'
) -> pd.DataFrame:
    """
    Merge STAI scores and filter participants without scores.
    
    Args:
        trials_df: DataFrame with participant IDs
        stai_df: DataFrame with participant IDs and STAI scores
        participant_col: Name of the participant ID column
        
    Returns:
        DataFrame with STAI scores merged and participants without scores removed
    """
    if participant_col not in stai_df.columns or participant_col not in trials_df.columns:
        raise ValueError(f"Participant column '{participant_col}' not found in one of the dataframes")
    
    if 'STAI_score' not in stai_df.columns:
        raise ValueError("STAI_score column not found in stai_df")
    
    # Merge
    merged = trials_df.merge(
        stai_df[[participant_col, 'STAI_score']], 
        on=participant_col, 
        how='left'
    )
    
    # Filter out participants without STAI scores
    before_count = len(merged)
    merged = merged.dropna(subset=['STAI_score'])
    after_count = len(merged)
    
    if before_count != after_count:
        logger.warning(f"Filtered out {before_count - after_count} participants without STAI scores")
    
    return merged.reset_index(drop=True)

def filter_trials(
    trials_df: pd.DataFrame, 
    eye_tracking_df: pd.DataFrame,
    max_missing_frames_pct: float = 0.5,
    max_blink_duration_ms: Optional[float] = None
) -> pd.DataFrame:
    """
    Filter trials based on missing data and blink duration.
    
    Args:
        trials_df: DataFrame with trial information
        eye_tracking_df: DataFrame with eye tracking data including blink markers
        max_missing_frames_pct: Maximum allowed percentage of missing frames
        max_blink_duration_ms: Maximum allowed blink duration in ms
        
    Returns:
        Filtered DataFrame of trials
    """
    if 'trial_id' not in trials_df.columns:
        raise ValueError("trials_df must contain 'trial_id' column")
    
    filtered_trials = []
    
    for trial_id, trial_group in trials_df.groupby('trial_id'):
        # Get eye tracking data for this trial
        trial_eye_data = eye_tracking_df[eye_tracking_df['trial_id'] == trial_id] if 'trial_id' in eye_tracking_df.columns else pd.DataFrame()
        
        # Check for missing frames (simplified: assume missing if no data or large gaps)
        if trial_eye_data.empty:
            logger.debug(f"Trial {trial_id}: No eye tracking data, excluding")
            continue
        
        # Calculate missing frames percentage (simplified)
        # In a real implementation, this would compare expected vs actual frames
        total_expected_frames = len(trial_group)  # Assuming trials_df has one row per frame
        actual_frames = len(trial_eye_data)
        
        if total_expected_frames > 0:
            missing_pct = 1.0 - (actual_frames / total_expected_frames)
            if missing_pct > max_missing_frames_pct:
                logger.debug(f"Trial {trial_id}: Missing frames {missing_pct:.2%} > {max_missing_frames_pct:.2%}, excluding")
                continue
        
        # Check blink duration if data available
        if max_blink_duration_ms is not None and 'blink_duration_ms' in trial_eye_data.columns:
            max_blink = trial_eye_data['blink_duration_ms'].max()
            if max_blink > max_blink_duration_ms:
                logger.debug(f"Trial {trial_id}: Max blink {max_blink}ms > {max_blink_duration_ms}ms, excluding")
                continue
        
        filtered_trials.append(trial_id)
    
    filtered_df = trials_df[trials_df['trial_id'].isin(filtered_trials)].reset_index(drop=True)
    logger.info(f"Filtered trials: {len(trials_df)} -> {len(filtered_df)}")
    
    return filtered_df

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the analysis CSV schema."""
    if schema_path is None:
        schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """Validate DataFrame against the schema."""
    required_columns = schema.get('required_columns', [])
    column_types = schema.get('column_types', {})
    
    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Check column types (simplified)
    for col, expected_type in column_types.items():
        if col in df.columns:
            actual_type = str(df[col].dtype)
            # Simple type mapping
            type_map = {
                'int64': 'integer',
                'float64': 'float',
                'object': 'string',
                'bool': 'boolean'
            }
            if expected_type not in ['integer', 'float', 'string', 'boolean']:
                continue  # Skip unknown types
            
            if type_map.get(actual_type) != expected_type:
                logger.warning(f"Column {col} has type {actual_type}, expected {expected_type}")
    
    # Check for null values in required columns
    for col in required_columns:
        if df[col].isnull().any():
            raise ValueError(f"Column {col} contains null values")
    
    logger.info("Schema validation passed")

def generate_analysis_csv(
    trials_df: pd.DataFrame,
    fixations_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> None:
    """
    Generate the final analysis-ready CSV.
    
    Args:
        trials_df: Processed trials DataFrame with valence and STAI
        fixations_df: Extracted fixations DataFrame
        output_path: Path for output CSV (default: data/processed/analysis.csv)
    """
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "analysis.csv"
    
    # Merge trials with fixation data
    # Aggregate fixation data per trial
    fixation_agg = fixations_df.groupby('trial_id').agg({
        'duration_ms': ['mean', 'std', 'sum', 'count'],
        'avg_x': 'mean',
        'avg_y': 'mean'
    }).reset_index()
    
    fixation_agg.columns = ['trial_id', 'fixation_duration_mean_ms', 'fixation_duration_std_ms', 
                            'total_fixation_duration_ms', 'fixation_count', 'avg_x', 'avg_y']
    
    # Merge with trials
    analysis_df = trials_df.merge(fixation_agg, on='trial_id', how='left')
    
    # Fill NaN for trials with no fixations
    analysis_df['fixation_duration_mean_ms'] = analysis_df['fixation_duration_mean_ms'].fillna(0)
    analysis_df['fixation_duration_std_ms'] = analysis_df['fixation_duration_std_ms'].fillna(0)
    analysis_df['total_fixation_duration_ms'] = analysis_df['total_fixation_duration_ms'].fillna(0)
    analysis_df['fixation_count'] = analysis_df['fixation_count'].fillna(0)
    analysis_df['avg_x'] = analysis_df['avg_x'].fillna(0)
    analysis_df['avg_y'] = analysis_df['avg_y'].fillna(0)
    
    # Select and order columns per schema
    schema = load_schema()
    required_columns = schema.get('required_columns', [])
    
    # Ensure all required columns are present
    for col in required_columns:
        if col not in analysis_df.columns:
            logger.warning(f"Required column {col} not found, adding as NaN (will fail validation)")
            analysis_df[col] = np.nan
    
    # Select columns
    final_columns = [col for col in required_columns if col in analysis_df.columns]
    # Add any extra columns from the schema that are optional
    optional_columns = [col for col in analysis_df.columns if col not in final_columns]
    final_columns.extend(optional_columns)
    
    analysis_df = analysis_df[final_columns]
    
    # Validate against schema
    validate_against_schema(analysis_df, schema)
    
    # Save to CSV
    analysis_df.to_csv(output_path, index=False)
    logger.info(f"Analysis CSV generated: {output_path} ({len(analysis_df)} rows)")

def main():
    """Main entry point for preprocessing pipeline."""
    parser = argparse.ArgumentParser(description="Preprocess RSVP dataset for analysis")
    parser.add_argument('--manifest', type=str, help='Path to manifest file')
    parser.add_argument('--min-fixation-ms', type=float, default=100.0, help='Minimum fixation duration in ms')
    parser.add_argument('--output', type=str, help='Path for output CSV')
    args = parser.parse_args()
    
    logger.info("Starting preprocessing pipeline")
    
    try:
        # Load manifest
        manifest = load_manifest(Path(args.manifest) if args.manifest else None)
        
        # Validate required variables
        required_vars = ['eye_tracking', 'valence', 'recall', 'STAI']
        validate_variables(manifest, required_vars)
        
        # Extract geometry metadata
        geometry = extract_geometry_metadata(manifest)
        
        # Calculate I-VT threshold
        ivt_threshold = calculate_ivt_threshold(geometry)
        
        # Load data files (simplified for this implementation)
        # In a real implementation, these would be loaded from data/raw/
        trials_df = pd.read_csv(DATA_RAW_DIR / "trials.csv")
        eye_tracking_df = pd.read_csv(DATA_RAW_DIR / "eye_tracking.csv")
        stai_df = pd.read_csv(DATA_RAW_DIR / "STAI_scores.csv")
        valence_map = pd.read_csv(DATA_RAW_DIR / "stimulus_valence_map.csv").set_index('stimulus_id')['valence'].to_dict()
        
        # Extract fixations
        fixations_df = extract_fixations_ivt(
            eye_tracking_df, 
            threshold_deg_s=ivt_threshold, 
            min_duration_ms=args.min_fixation_ms
        )
        
        # Map stimulus valence
        trials_df = map_stimulus_valence(trials_df, valence_map)
        
        # Merge STAI scores
        trials_df = merge_stai_scores(trials_df, stai_df)
        
        # Filter trials
        trials_df = filter_trials(trials_df, eye_tracking_df)
        
        # Generate analysis CSV
        generate_analysis_csv(trials_df, fixations_df, Path(args.output) if args.output else None)
        
        logger.info("Preprocessing pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
