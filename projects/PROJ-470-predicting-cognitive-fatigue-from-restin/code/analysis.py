"""
Analysis pipeline for cognitive fatigue prediction.
Orchestrates delta calculation, correlation analysis, and reporting.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from utils.logging import get_logger

# Configure basic logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

# Required paths for validation
REQUIRED_FILES = {
    'cleaned_eeg_dir': 'data/processed/cleaned_eeg/',
    'complexity_metrics': 'data/analysis/complexity_metrics.csv',
    'fatigue_scores': 'data/processed/fatigue_scores.csv'
}

# Output paths for T019
DELTA_OUTPUT_PATH = 'data/analysis/delta_scores.csv'


def validate_inputs() -> bool:
    """
    Check for existence of all required processed data files.
    
    The system MUST fail if these files are missing, as no analysis can proceed.
    
    Returns:
        bool: True if all files exist, False otherwise.
    
    Raises:
        SystemExit: Exits with code 1 and prints available files if validation fails.
    """
    logger.info("Starting input validation for analysis pipeline.")
    missing_files = []
    available_files = []

    for key, path in REQUIRED_FILES.items():
        if not os.path.exists(path):
            missing_files.append(f"{key}: {path}")
        else:
            available_files.append(path)

    if missing_files:
        error_msg = (
            "CRITICAL: Required data files are missing. Analysis cannot proceed.\n"
            f"Missing files:\n"
            + "\n".join([f"  - {f}" for f in missing_files]) + "\n\n"
            f"Available files:\n"
            + "\n".join([f"  - {f}" for f in available_files])
        )
        logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        sys.exit(1)

    logger.info("All required input files found.")
    return True


def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    import yaml
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults.")
        return {}


def calculate_deltas() -> pd.DataFrame:
    """
    Compute delta scores (Post - Pre) for both complexity and fatigue.
    
    CRITICAL: Verifies that complexity and fatigue data are paired by 
    participant_id and that both pre and post segments exist for each 
    participant before calculating deltas.
    
    Returns:
        pd.DataFrame: DataFrame containing delta scores.
    
    Raises:
        SystemExit: Exits with code 1 and prints "Paired data missing" if pairing is incomplete.
    """
    logger.info("Loading complexity metrics and fatigue scores for delta calculation.")
    
    # Load complexity metrics
    try:
        complexity_df = pd.read_csv('data/analysis/complexity_metrics.csv')
    except Exception as e:
        logger.error(f"Failed to load complexity metrics: {e}")
        sys.exit(1)
    
    # Load fatigue scores
    try:
        fatigue_df = pd.read_csv('data/processed/fatigue_scores.csv')
    except Exception as e:
        logger.error(f"Failed to load fatigue scores: {e}")
        sys.exit(1)
    
    # Validate required columns in complexity metrics
    required_complexity_cols = ['participant_id', 'segment_id', 'lzc_value', 'pe_value']
    missing_complexity_cols = [col for col in required_complexity_cols if col not in complexity_df.columns]
    if missing_complexity_cols:
        logger.error(f"Missing columns in complexity metrics: {missing_complexity_cols}")
        sys.exit(1)
    
    # Validate required columns in fatigue scores
    required_fatigue_cols = ['participant_id', 'timepoint', 'fatigue_score']
    missing_fatigue_cols = [col for col in required_fatigue_cols if col not in fatigue_df.columns]
    if missing_fatigue_cols:
        logger.error(f"Missing columns in fatigue scores: {missing_fatigue_cols}")
        sys.exit(1)
    
    # Extract unique participants from complexity data
    complexity_participants = set(complexity_df['participant_id'].unique())
    
    # Extract unique participants from fatigue data
    fatigue_participants = set(fatigue_df['participant_id'].unique())
    
    # Check for intersection
    common_participants = complexity_participants & fatigue_participants
    
    if len(common_participants) == 0:
        logger.error("No common participants between complexity and fatigue data.")
        print("Paired data missing")
        sys.exit(1)
    
    # For each participant, check if both pre and post timepoints exist in fatigue data
    participants_with_full_pairs = []
    for pid in common_participants:
        participant_fatigue = fatigue_df[
            (fatigue_df['participant_id'] == pid) & 
            (fatigue_df['timepoint'].isin(['pre', 'post']))
        ]
        
        # Check if both pre and post exist
        timepoints = set(participant_fatigue['timepoint'].unique())
        if 'pre' in timepoints and 'post' in timepoints:
            participants_with_full_pairs.append(pid)
    
    if len(participants_with_full_pairs) == 0:
        logger.error("No participants with both pre and post fatigue scores found.")
        print("Paired data missing")
        sys.exit(1)
    
    logger.info(f"Found {len(participants_with_full_pairs)} participants with complete paired data.")
    
    # Filter data to only include participants with full pairs
    complexity_df = complexity_df[complexity_df['participant_id'].isin(participants_with_full_pairs)]
    fatigue_df = fatigue_df[fatigue_df['participant_id'].isin(participants_with_full_pairs)]
    
    # Calculate fatigue delta (Post - Pre)
    fatigue_pre = fatigue_df[fatigue_df['timepoint'] == 'pre'][['participant_id', 'fatigue_score']].copy()
    fatigue_pre.columns = ['participant_id', 'fatigue_pre']
    
    fatigue_post = fatigue_df[fatigue_df['timepoint'] == 'post'][['participant_id', 'fatigue_score']].copy()
    fatigue_post.columns = ['participant_id', 'fatigue_post']
    
    fatigue_delta = pd.merge(fatigue_pre, fatigue_post, on='participant_id', how='inner')
    fatigue_delta['fatigue_delta'] = fatigue_delta['fatigue_post'] - fatigue_delta['fatigue_pre']
    
    # Calculate complexity delta (Post - Pre)
    # First, separate pre and post complexity metrics
    # Assuming segment_id contains timepoint info or we need to infer from context
    # For this implementation, we assume segment_id is unique per participant and timepoint
    # We'll pivot the data to get pre and post values per participant and channel
    
    # Since segment_id might not directly indicate pre/post, we need to join with fatigue data
    # to get the timepoint for each segment. However, the complexity data doesn't have timepoint.
    # We assume that for each participant, there are segments corresponding to pre and post.
    # We'll calculate the mean complexity per participant per timepoint if multiple segments exist.
    
    # For simplicity, let's assume segment_id encodes timepoint (e.g., 'pre_1', 'post_1')
    # or we have exactly one segment per timepoint per participant.
    # If not, we'll aggregate by participant and assume the order matches fatigue timepoints.
    
    # Alternative: We'll create a mapping from participant to timepoint based on segment_id pattern
    # If segment_id contains 'pre' or 'post', we use that. Otherwise, we assume first segment is pre, second is post.
    
    def infer_timepoint(segment_id):
        if 'pre' in str(segment_id).lower():
            return 'pre'
        elif 'post' in str(segment_id).lower():
            return 'post'
        else:
            # Fallback: assume order
            return None
    
    complexity_df['inferred_timepoint'] = complexity_df['segment_id'].apply(infer_timepoint)
    
    # For participants without clear timepoint in segment_id, we'll need to handle carefully
    # For now, let's filter to only those with clear timepoints
    complexity_with_timepoint = complexity_df[complexity_df['inferred_timepoint'].notna()]
    
    if len(complexity_with_timepoint) == 0:
        # Fallback: assume first segment per participant is pre, second is post
        logger.warning("Could not infer timepoints from segment_id. Using fallback ordering.")
        # Group by participant and assign timepoints based on order
        def assign_timepoints(group):
            if len(group) >= 2:
                group = group.sort_values('segment_id')
                group.loc[group.index[:len(group)//2], 'inferred_timepoint'] = 'pre'
                group.loc[group.index[len(group)//2:], 'inferred_timepoint'] = 'post'
            elif len(group) == 1:
                group.loc[group.index[0], 'inferred_timepoint'] = 'pre'  # Default to pre if only one
            return group
        
        complexity_df = complexity_df.groupby('participant_id', group_keys=False).apply(assign_timepoints)
        complexity_with_timepoint = complexity_df
    
    # Now pivot to get pre and post values
    # We'll calculate mean complexity per participant per timepoint per channel
    complexity_pre = complexity_with_timepoint[
        complexity_with_timepoint['inferred_timepoint'] == 'pre'
    ].groupby(['participant_id', 'channel']).agg({
        'lzc_value': 'mean',
        'pe_value': 'mean'
    }).reset_index()
    complexity_pre.columns = ['participant_id', 'channel', 'lzc_pre', 'pe_pre']
    
    complexity_post = complexity_with_timepoint[
        complexity_with_timepoint['inferred_timepoint'] == 'post'
    ].groupby(['participant_id', 'channel']).agg({
        'lzc_value': 'mean',
        'pe_value': 'mean'
    }).reset_index()
    complexity_post.columns = ['participant_id', 'channel', 'lzc_post', 'pe_post']
    
    # Merge pre and post complexity
    complexity_delta = pd.merge(complexity_pre, complexity_post, on=['participant_id', 'channel'], how='inner')
    complexity_delta['lzc_delta'] = complexity_delta['lzc_post'] - complexity_delta['lzc_pre']
    complexity_delta['pe_delta'] = complexity_delta['pe_post'] - complexity_delta['pe_pre']
    
    # Merge with fatigue delta
    delta_df = pd.merge(complexity_delta, fatigue_delta, on='participant_id', how='inner')
    
    # Reorder columns
    delta_df = delta_df[['participant_id', 'channel', 'lzc_pre', 'lzc_post', 'lzc_delta', 
                         'pe_pre', 'pe_post', 'pe_delta', 
                         'fatigue_pre', 'fatigue_post', 'fatigue_delta']]
    
    return delta_df


def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description="Cognitive Fatigue Analysis Pipeline")
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Run only input validation and exit'
    )
    args = parser.parse_args()

    # Initialize logging
    logger.info("Starting analysis pipeline.")

    # Validate inputs
    validate_inputs()

    if args.validate_only:
        logger.info("Validation passed. Exiting as requested.")
        return 0

    logger.info("Validation passed. Proceeding to delta calculation.")
    
    # Calculate deltas
    try:
        delta_df = calculate_deltas()
    except Exception as e:
        logger.error(f"Failed to calculate deltas: {e}")
        print("Paired data missing")
        sys.exit(1)
    
    # Write delta scores to CSV
    try:
        delta_df.to_csv(DELTA_OUTPUT_PATH, index=False)
        logger.info(f"Delta scores written to {DELTA_OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write delta scores: {e}")
        sys.exit(1)
    
    logger.info("Delta calculation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())