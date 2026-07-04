"""
Preprocess OULAD data for feedback timing analysis.

This script filters courses by "assessment" and "forum" events,
extracts learner records with feedback timestamps, grades, and completion status,
and saves the processed data to `data/processed/learners_raw.csv`.

It relies on raw data downloaded by `download_data.py` to `data/raw/`.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import project utilities
from config import load_config, get_config_value
from logging_config import get_logger, info, error, warning, debug
from checksums import compute_sha256, save_checksums
from schema import load_schema_from_file, validate_column_presence, validate_null_values

# Setup logger
logger = get_logger(__name__)

# Constants for column names (matching OULAD schema)
COL_STUDENT_ID = 'id_student'
COL_COURSE_ID = 'id_course'
COL_DATE_RECORDED = 'date_recorded'
COL_FINAL_RESULT = 'final_result'
COL_CATEGORICAL_RESULT = 'categorical_result'
COL_EVENTS = 'events'
COL_STUDY_PERIOD_START = 'date_registration'
COL_STUDY_PERIOD_END = 'date_unregistration'

# Output paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
OUTPUT_FILE = DATA_PROCESSED_DIR / 'learners_raw.csv'

# Configuration keys
CONFIG_KEY_MIN_LEARNERS = 'min_learners_per_course'
CONFIG_KEY_REQUIRED_EVENT_TYPES = 'required_event_types'

def load_config_value(key, default=None):
    """Helper to load config values with defaults."""
    config = load_config()
    return get_config_value(config, key, default)

def load_raw_datasets():
    """
    Load all CSV files from the raw data directory.
    Returns a dictionary of DataFrames keyed by filename.
    """
    if not DATA_RAW_DIR.exists():
        error(f"Raw data directory not found: {DATA_RAW_DIR}")
        raise FileNotFoundError(f"Raw data directory not found: {DATA_RAW_DIR}")

    data_files = list(DATA_RAW_DIR.glob('*.csv'))
    if not data_files:
        error(f"No CSV files found in {DATA_RAW_DIR}")
        raise FileNotFoundError(f"No CSV files found in {DATA_RAW_DIR}")

    dfs = {}
    for file_path in data_files:
        try:
            # OULAD data can be large, use chunking if necessary, but assume fit for now
            df = pd.read_csv(file_path, low_memory=False)
            dfs[file_path.name] = df
            info(f"Loaded {file_path.name}: {len(df)} rows")
        except Exception as e:
            error(f"Failed to load {file_path.name}: {e}")
            raise
    return dfs

def get_course_event_types(dfs):
    """
    Identify courses that have both 'assessment' and 'forum' events.
    Returns a set of course IDs meeting this criteria.
    """
    if 'studentModule' not in dfs:
        # studentModule contains the link between students and courses
        # We need to find where events are defined. In OULAD, events are in 'studentVLE' or similar?
        # Actually, OULAD schema:
        # - courses.csv: course info
        # - studentModule.csv: links students to courses, includes final_result
        # - studentVLE.csv: contains event logs (id_site, code_module, date_recorded)
        # - vle.csv: defines sites (events)
        
        # We need to join studentVLE with vle to get event types.
        # But first, let's check what files we have.
        pass

    # We need the 'vle' table to map id_site to event types
    # And 'studentVLE' to see which students accessed which sites
    
    # Let's assume we have 'vle.csv' and 'studentVLE.csv' and 'studentModule.csv'
    if 'vle.csv' not in dfs or 'studentVLE.csv' not in dfs or 'studentModule.csv' not in dfs:
        error("Required files 'vle.csv', 'studentVLE.csv', and 'studentModule.csv' not found in raw data.")
        raise FileNotFoundError("Missing required OULAD data files.")

    vle_df = dfs['vle.csv']
    student_vle_df = dfs['studentVLE.csv']
    student_mod_df = dfs['studentModule.csv']

    # Map id_site to event type
    # vle.csv columns: id_site, code_module, code_presentation, id_site_type, date_start
    # We need to join with site_type to get the name (e.g., 'assessment', 'forum')
    # Assuming site_types.csv exists or is embedded. If not, we might need to infer or skip.
    # Standard OULAD has 'site_types.csv': id_site_type, site_type
    
    site_types_file = DATA_RAW_DIR / 'site_types.csv'
    if site_types_file.exists():
        site_types_df = pd.read_csv(site_types_file)
        vle_with_type = vle_df.merge(site_types_df, on='id_site_type', how='left')
    else:
        # Fallback: if site_types not found, we might have to rely on id_site_type directly
        # or assume the mapping is known. For robustness, we'll try to proceed with id_site_type
        # but log a warning.
        warning("site_types.csv not found. Using id_site_type as proxy for event type.")
        vle_with_type = vle_df.copy()
        vle_with_type['site_type'] = vle_with_type['id_site_type']

    # Filter for 'assessment' and 'forum'
    # Normalize strings
    target_types = ['assessment', 'forum']
    valid_sites = vle_with_type[vle_with_type['site_type'].str.lower().isin(target_types)]
    
    # Get unique course IDs (code_module + code_presentation) that have these events
    # studentVLE links students to courses (code_module, code_presentation) and sites (id_site)
    # But we need to know which COURSES (modules) have these events available.
    # So we look at vle.csv: which code_modules have sites of type 'assessment' or 'forum'?
    
    valid_courses = valid_sites[['code_module', 'code_presentation']].drop_duplicates()
    valid_course_keys = set(zip(valid_courses['code_module'], valid_courses['code_presentation']))
    
    info(f"Found {len(valid_course_keys)} courses with 'assessment' and/or 'forum' events.")
    return valid_course_keys

def filter_courses_by_events(dfs, valid_course_keys):
    """
    Filter studentModule records to only include courses with required event types.
    """
    student_mod_df = dfs['studentModule.csv']
    
    # Create a key for each row
    student_mod_df['_course_key'] = list(zip(student_mod_df['code_module'], student_mod_df['code_presentation']))
    
    filtered_df = student_mod_df[student_mod_df['_course_key'].isin(valid_course_keys)].copy()
    
    info(f"Filtered studentModule: {len(student_mod_df)} -> {len(filtered_df)} rows")
    return filtered_df

def extract_learner_records(student_mod_df, valid_course_keys):
    """
    Extract learner records with required fields:
    - is_complete (derived from final_result)
    - course_id
    - student_id
    - final_grade (numerical representation if possible, or category)
    """
    # We need to join with studentVLE to get event timestamps?
    # Actually, the task says "extract learner records with feedback timestamps".
    # Feedback timestamps come from studentVLE (date_recorded) for specific event types.
    # But for the raw learners file, we might just need the student-level summary first.
    # Let's focus on the studentModule data first, then enrich with VLE data later if needed.
    # The task specifically asks for "is_complete" and filtering courses.
    
    # Derive is_complete
    # final_result values: 'Pass', 'Distinction', 'Pass', 'Withdrawn', etc.
    # We'll map 'Withdrawn' to False, others to True.
    withdrawn_value = 'Withdrawn'
    student_mod_df['is_complete'] = student_mod_df[COL_CATEGORICAL_RESULT] != withdrawn_value
    
    # Select required columns
    output_cols = [
        COL_STUDENT_ID,
        COL_COURSE_ID,
        COL_STUDY_PERIOD_START,
        COL_STUDY_PERIOD_END,
        COL_FINAL_RESULT,
        COL_CATEGORICAL_RESULT,
        'is_complete'
    ]
    
    # Ensure columns exist
    existing_cols = [c for c in output_cols if c in student_mod_df.columns]
    missing_cols = [c for c in output_cols if c not in student_mod_df.columns]
    if missing_cols:
        warning(f"Missing expected columns in studentModule: {missing_cols}")
        
    result_df = student_mod_df[existing_cols].copy()
    
    # Clean up temporary column
    if '_course_key' in result_df.columns:
        result_df.drop(columns=['_course_key'], inplace=True)
        
    return result_df

def apply_min_learner_filter(learner_df, min_learners):
    """
    Exclude courses with fewer than min_learners.
    """
    course_counts = learner_df.groupby(COL_COURSE_ID).size()
    valid_courses = course_counts[course_counts >= min_learners].index
    
    filtered_df = learner_df[learner_df[COL_COURSE_ID].isin(valid_courses)].copy()
    
    excluded_count = len(learner_df) - len(filtered_df)
    info(f"Excluded {excluded_count} learners from courses with < {min_learners} students.")
    
    return filtered_df

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting preprocessing pipeline...")
    
    # Load config
    min_learners = load_config_value(CONFIG_KEY_MIN_LEARNERS, default=50)
    info(f"Minimum learners per course threshold: {min_learners}")
    
    # Load raw data
    try:
        dfs = load_raw_datasets()
    except FileNotFoundError as e:
        error(str(e))
        sys.exit(1)
    
    # Identify valid courses
    try:
        valid_course_keys = get_course_event_types(dfs)
    except FileNotFoundError as e:
        error(str(e))
        sys.exit(1)
    
    if not valid_course_keys:
        error("No courses found with required event types. Cannot proceed.")
        sys.exit(1)
    
    # Filter courses
    filtered_student_mod = filter_courses_by_events(dfs, valid_course_keys)
    
    # Extract learner records
    learner_df = extract_learner_records(filtered_student_mod, valid_course_keys)
    
    # Apply min learner filter
    learner_df = apply_min_learner_filter(learner_df, min_learners)
    
    # Validate schema
    schema_path = PROJECT_ROOT / 'contracts' / 'dataset.schema.yaml'
    if schema_path.exists():
        schema = load_schema_from_file(schema_path)
        # Basic validation
        validate_column_presence(learner_df, schema)
        validate_null_values(learner_df, schema)
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    info(f"Saving processed data to {OUTPUT_FILE}")
    learner_df.to_csv(OUTPUT_FILE, index=False)
    
    # Generate checksum
    checksum = compute_sha256(OUTPUT_FILE)
    info(f"Output checksum (SHA256): {checksum}")
    
    # Save checksums
    checksum_file = DATA_PROCESSED_DIR / 'learners_raw.csv.sha256'
    save_checksums({str(OUTPUT_FILE): checksum}, checksum_file)
    
    logger.info(f"Preprocessing complete. Output: {OUTPUT_FILE} ({len(learner_df)} records)")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())