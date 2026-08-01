import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import local utilities
from config import load_config, get_config_value
from logging_config import get_logger, info, warning, error, debug
from checksums import generate_checksum_for_file

# Initialize logger
logger = get_logger(__name__)

def load_config_value(key, default=None):
    """Helper to load a specific config value."""
    config = load_config()
    return get_config_value(config, key, default)

def load_raw_datasets(data_dir: Path) -> pd.DataFrame:
    """
    Load the raw learner datasets from the data directory.
    Expects the pre-downloaded OULAD data files (vle, assessments, etc.)
    to be merged into a single raw dataframe or loaded from a specific
    intermediate file if T016/T017 produced one.
    
    For this implementation, we assume T016/T017 produced 'data/processed/learners_raw_stage1.csv'
    or we load from the raw zip structure if needed. 
    Given T016/T017 context, we assume a raw merged file exists or we simulate the 
    loading of the 'vle' and 'assessments' tables to construct the learner view.
    
    To strictly follow "Real Data Only", we attempt to load the raw CSVs 
    that T016 (download) and T017 (preprocess) would have produced.
    """
    # Check for intermediate raw file from previous steps
    intermediate_path = data_dir / "processed" / "learners_raw_stage1.csv"
    if intermediate_path.exists():
        logger.info(f"Loading intermediate raw data from {intermediate_path}")
        return pd.read_csv(intermediate_path)
    
    # Fallback: Try to load raw CSVs directly if intermediate doesn't exist
    # This handles the case where T016/T017 might have written to 'raw' directly
    vle_path = data_dir / "raw" / "vle.csv"
    if vle_path.exists():
        logger.info("Loading raw vle.csv directly")
        vle = pd.read_csv(vle_path)
        # Basic schema check
        if 'code_module' not in vle.columns or 'id_student' not in vle.columns:
            error("Raw vle.csv missing expected columns")
            raise ValueError("Invalid raw data format")
        return vle
    
    error("No raw data source found. Ensure T016/T017 have run.")
    raise FileNotFoundError("Raw data not found")

def get_course_event_types(df: pd.DataFrame) -> dict:
    """
    Analyze the dataframe to determine which courses have 'assessment' and 'forum' events.
    Returns a dict mapping course_id -> has_assessment, has_forum.
    """
    # Assuming 'event_type' or 'code_module' + 'event' columns exist.
    # OULAD data usually has 'code_module' and 'date'.
    # We assume T017 has already added an 'event_type' column or we infer from 'event' column.
    
    # If 'event_type' column exists:
    if 'event_type' in df.columns:
        course_events = df.groupby('code_module')['event_type'].apply(set).to_dict()
    else:
        # Fallback: assume 'event' column contains strings like 'assessment', 'forum'
        if 'event' in df.columns:
            course_events = df.groupby('code_module')['event'].apply(set).to_dict()
        else:
            warning("No 'event_type' or 'event' column found. Cannot filter by event type.")
            return {}

    result = {}
    for course, events in course_events.items():
        # Normalize to lowercase for comparison
        events_lower = {str(e).lower() for e in events}
        has_assessment = 'assessment' in events_lower
        has_forum = 'forum' in events_lower
        if has_assessment and has_forum:
            result[course] = True
        else:
            result[course] = False
    
    return result

def filter_courses_by_events(df: pd.DataFrame, valid_courses: dict) -> pd.DataFrame:
    """
    Filter the dataframe to keep only rows where code_module is in valid_courses.
    """
    valid_list = [k for k, v in valid_courses.items() if v]
    if not valid_list:
        warning("No courses with both assessment and forum events found.")
        return pd.DataFrame()
    
    filtered = df[df['code_module'].isin(valid_list)]
    logger.info(f"Filtered to {len(valid_list)} courses with assessment and forum events.")
    return filtered

def extract_learner_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract learner records with required fields:
    - id_student
    - code_module
    - final_result (or equivalent)
    - is_complete (derived from final_result or a specific flag)
    - forum_interaction_count (to be used in T018)
    - feedback_timestamps (if available)
    
    This function prepares the base dataframe for subsequent filtering steps.
    """
    # Ensure necessary columns exist
    required = ['id_student', 'code_module', 'final_result']
    missing = [c for c in required if c not in df.columns]
    if missing:
        error(f"Missing required columns: {missing}")
        raise ValueError(f"Missing columns: {missing}")
    
    # Derive is_complete
    if 'is_complete' not in df.columns:
        # Assume 'Pass' or 'Distinction' or 'Pass' in final_result implies completion
        # OULAD 'final_result' often has: Pass, Distinction, Fail, Withdrawn, etc.
        df['is_complete'] = df['final_result'].isin(['Pass', 'Distinction', 'Pass with Distinction'])
    
    # Count forum interactions per learner (needed for T018)
    # Assuming 'event_type' or 'event' column exists
    if 'event_type' in df.columns:
        forum_mask = df['event_type'].str.lower() == 'forum'
        forum_counts = df[forum_mask].groupby(['id_student', 'code_module']).size().reset_index(name='forum_count')
        df = df.merge(forum_counts, on=['id_student', 'code_module'], how='left')
        df['forum_count'] = df['forum_count'].fillna(0)
    elif 'event' in df.columns:
        forum_mask = df['event'].str.lower() == 'forum'
        forum_counts = df[forum_mask].groupby(['id_student', 'code_module']).size().reset_index(name='forum_count')
        df = df.merge(forum_counts, on=['id_student', 'code_module'], how='left')
        df['forum_count'] = df['forum_count'].fillna(0)
    else:
        df['forum_count'] = 0
        warning("Could not calculate forum counts; defaulting to 0.")
    
    # Select relevant columns
    cols = [c for c in df.columns if c in ['id_student', 'code_module', 'final_result', 'is_complete', 'forum_count', 'date', 'event_type', 'event']]
    return df[cols].drop_duplicates()

def apply_min_learner_filter(df: pd.DataFrame, min_learners: int = 50) -> pd.DataFrame:
    """
    Exclude courses with fewer than min_learners unique students.
    Logs the exclusion count and the excluded course IDs.
    
    Args:
        df: DataFrame with 'id_student' and 'code_module' columns.
        min_learners: Minimum number of unique learners required per course.
    
    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Applying minimum learner filter (min={min_learners})...")
    
    # Count unique learners per course
    learner_counts = df.groupby('code_module')['id_student'].nunique().reset_index()
    learner_counts.columns = ['code_module', 'learner_count']
    
    # Identify courses to keep
    valid_courses = learner_counts[learner_counts['learner_count'] >= min_learners]
    excluded_courses = learner_counts[learner_counts['learner_count'] < min_learners]
    
    excluded_count = len(excluded_courses)
    included_count = len(valid_courses)
    
    logger.info(f"Total courses before filter: {len(learner_counts)}")
    logger.info(f"Courses excluded (< {min_learners} learners): {excluded_count}")
    logger.info(f"Courses included: {included_count}")
    
    if excluded_count > 0:
        excluded_list = excluded_courses['code_module'].tolist()
        debug(f"Excluded course IDs: {excluded_list}")
    
    # Filter the main dataframe
    valid_course_ids = valid_courses['code_module'].tolist()
    filtered_df = df[df['code_module'].isin(valid_course_ids)]
    
    return filtered_df

def save_filtered_data(df: pd.DataFrame, output_path: Path):
    """
    Save the filtered dataframe to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path} ({len(df)} records)")

def main():
    """
    Main entry point for the preprocessing pipeline.
    Orchestrates:
    1. Load raw data
    2. Filter by event types (Assessment + Forum)
    3. Extract learner records
    4. Exclude learners with no forum interactions (T018 logic)
    5. Exclude courses with <50 learners (T019 logic)
    6. Save final output
    """
    logger.info("Starting preprocessing pipeline (T017 + T018 + T019)...")
    
    # Paths
    data_dir = Path("data")
    raw_output = data_dir / "processed" / "learners_raw_stage1.csv"
    final_output = data_dir / "processed" / "learners_raw.csv"
    
    # 1. Load raw data
    try:
        df = load_raw_datasets(data_dir)
        logger.info(f"Loaded {len(df)} raw records.")
    except Exception as e:
        error(f"Failed to load raw data: {e}")
        # If data is missing, we cannot proceed. 
        # In a real run, this would exit. 
        # For this task, we assume T016/T017 produced the data.
        sys.exit(1)

    # 2. Filter by event types
    course_events = get_course_event_types(df)
    df = filter_courses_by_events(df, course_events)
    
    if df.empty:
        error("No data remaining after event type filtering.")
        sys.exit(1)

    # 3. Extract learner records
    df = extract_learner_records(df)
    
    # 4. Exclude learners with no forum interactions (T018)
    # Filter out rows where forum_count is 0
    initial_count = len(df)
    df = df[df['forum_count'] > 0]
    excluded_learners = initial_count - len(df)
    logger.info(f"T018: Excluded {excluded_learners} learner records with no forum interactions.")
    
    if df.empty:
        error("No data remaining after forum interaction filtering.")
        sys.exit(1)

    # 5. Exclude courses with <50 learners (T019)
    # This is the core requirement for T019
    min_learners = load_config_value("min_learners_per_course", 50)
    df = apply_min_learner_filter(df, min_learners)
    
    if df.empty:
        error("No data remaining after minimum learner filter.")
        sys.exit(1)

    # 6. Save output
    save_filtered_data(df, final_output)
    
    # Generate checksum
    checksum_path = data_dir / "checksums" / "learners_raw.csv.sha256"
    generate_checksum_for_file(final_output, checksum_path)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return df

if __name__ == "__main__":
    main()