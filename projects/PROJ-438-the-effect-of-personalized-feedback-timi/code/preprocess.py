import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Import from existing project modules
from config import load_config, get_data_paths, get_oulad_urls
from schema import validate_schema, load_schema_and_validate
from checksums import compute_sha256, generate_checksum_for_file
from logging_config import setup_logger, get_logger, info, warning, error, debug

def load_config_value(key, config=None):
    """Helper to extract a config value."""
    if config is None:
        config = load_config()
    return config.get(key)

def load_raw_datasets(data_root: Path, urls: dict) -> tuple:
    """
    Load raw student and assessment event data from the downloaded files.
    Returns (students_df, events_df)
    """
    students_path = data_root / "students_data.csv"
    events_path = data_root / "train.parquet" # Assuming parquet based on typical OULAD structure or CSV if specified

    if not students_path.exists():
        raise FileNotFoundError(f"Raw students data not found at {students_path}. Run download_data.py first.")
    
    # Load students
    students_df = pd.read_csv(students_path)
    info(f"Loaded {len(students_df)} student records from {students_path}")

    # Load events
    if events_path.suffix == '.parquet':
        events_df = pd.read_parquet(events_path)
    else:
        events_df = pd.read_csv(events_path)
    
    info(f"Loaded {len(events_df)} event records from {events_path}")
    
    # Ensure required columns exist
    required_students = ['id_student', 'code_module', 'code_presentation', 'final_result', 'date_registered']
    required_events = ['id_student', 'code_module', 'code_presentation', 'event_type', 'timestamp', 'date']

    for col in required_students:
        if col not in students_df.columns:
            raise ValueError(f"Missing required column '{col}' in students data")
    
    for col in required_events:
        if col not in events_df.columns:
            raise ValueError(f"Missing required column '{col}' in events data")

    return students_df, events_df

def get_course_event_types(events_df: pd.DataFrame, course_ids: list, event_types: list) -> pd.DataFrame:
    """
    Filter events to only include specific event types (e.g., 'submission', 'forum') for given courses.
    """
    mask = (events_df['code_module'].isin(course_ids)) & (events_df['event_type'].isin(event_types))
    return events_df[mask]

def filter_courses_by_events(students_df: pd.DataFrame, events_df: pd.DataFrame, required_types: list) -> list:
    """
    Identify courses that have at least one record of each required event type.
    Returns list of valid (code_module, code_presentation) tuples.
    """
    # Get unique course combinations that have all required event types
    valid_courses = []
    
    # Group by course and check event types
    course_events = events_df.groupby(['code_module', 'code_presentation'])['event_type'].apply(set).reset_index()
    
    for _, row in course_events.iterrows():
        module, presentation = row['code_module'], row['code_presentation']
        event_set = row['event_type']
        
        if all(t in event_set for t in required_types):
            valid_courses.append((module, presentation))
    
    info(f"Found {len(valid_courses)} courses with all required event types: {required_types}")
    return valid_courses

def extract_learner_records(students_df: pd.DataFrame, events_df: pd.DataFrame, valid_courses: list) -> pd.DataFrame:
    """
    Merge student and event data for valid courses.
    Returns a DataFrame with learner records including timestamps and grades.
    """
    # Filter students to valid courses
    valid_mask = students_df.apply(
        lambda row: (row['code_module'], row['code_presentation']) in valid_courses, axis=1
    )
    filtered_students = students_df[valid_mask].copy()
    
    # Filter events to valid courses
    valid_course_mask = events_df.apply(
        lambda row: (row['code_module'], row['code_presentation']) in valid_courses, axis=1
    )
    filtered_events = events_df[valid_course_mask].copy()

    # Ensure timestamp columns are datetime
    if 'date' in filtered_events.columns:
        filtered_events['timestamp'] = pd.to_datetime(filtered_events['date'], errors='coerce')
    
    # Merge to get student details with events
    # We need to keep events to calculate intervals later, so we return the merged event-level data
    # But for the "learner record" in T017, we need to ensure they have events.
    
    # Join events with student final results
    merged = filtered_events.merge(
        filtered_students[['id_student', 'code_module', 'code_presentation', 'final_result']],
        on=['id_student', 'code_module', 'code_presentation'],
        how='left'
    )
    
    return merged

def apply_min_learner_filter(merged_df: pd.DataFrame, min_learners: int = 50) -> pd.DataFrame:
    """
    Exclude courses with fewer than min_learners unique students.
    Returns filtered DataFrame.
    """
    course_counts = merged_df.groupby(['code_module', 'code_presentation'])['id_student'].nunique()
    valid_courses = course_counts[course_counts >= min_learners].index.tolist()
    
    filtered = merged_df[merged_df.apply(
        lambda row: (row['code_module'], row['code_presentation']) in valid_courses, axis=1
    )]
    
    excluded_count = len(merged_df) - len(filtered)
    info(f"Excluded {excluded_count} records from courses with < {min_learners} learners")
    return filtered

def save_filtered_data(df: pd.DataFrame, output_path: Path, exclusion_log_path: Path, exclusion_counts: dict):
    """
    Save the filtered dataframe and write exclusion counts to log.
    """
    df.to_csv(output_path, index=False)
    info(f"Saved filtered data to {output_path}")
    
    # Write exclusion log
    with open(exclusion_log_path, 'w') as f:
        f.write(f"Exclusion Log - {datetime.now().isoformat()}\n")
        f.write("=" * 50 + "\n")
        for key, count in exclusion_counts.items():
            f.write(f"{key}: {count}\n")
        f.write(f"Total records remaining: {len(df)}\n")
    
    info(f"Exclusion log written to {exclusion_log_path}")

def main():
    logger = setup_logger("preprocess")
    info("Starting preprocessing pipeline (T017)")
    
    # Load config
    config = load_config()
    data_paths = get_data_paths(config)
    urls = get_oulad_urls(config)
    
    data_root = Path(data_paths['raw'])
    processed_dir = Path(data_paths['processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load raw data
    try:
        students_df, events_df = load_raw_datasets(data_root, urls)
    except FileNotFoundError as e:
        error(f"Data download failed: {e}")
        sys.exit(1)
    
    exclusion_counts = {
        "initial_students": len(students_df),
        "initial_events": len(events_df),
        "no_forum_interactions": 0,
        "no_submission_response": 0,
        "small_courses": 0,
        "final_count": 0
    }
    
    # 2. Filter courses by required events (submission + forum)
    # We assume 'submission' and 'forum' are the event types in OULAD
    required_types = ['submission', 'forum'] 
    valid_courses = filter_courses_by_events(students_df, events_df, required_types)
    
    if not valid_courses:
        error("No courses found with both submission and forum events.")
        sys.exit(1)
    
    # 3. Extract learner records for these courses
    merged_df = extract_learner_records(students_df, events_df, valid_courses)
    
    # 4. CRITICAL: Exclude learners with no subsequent event (no response)
    # We need to find learners who have a submission but NO subsequent event (e.g. forum post or another submission)
    # The task says: "Exclude learners who have a submission but NO subsequent event (no response)"
    # This implies we look for students who ONLY have submissions and nothing else? 
    # Or students who have a submission but no event AFTER it?
    # Interpretation: We need to ensure every student has at least one 'response' event after a submission.
    # Since OULAD data structure: 'submission' is the event, 'forum' is the response?
    # Let's assume we need at least one 'forum' event for every student who has a 'submission'.
    
    # Group by student to check event types
    student_events = merged_df.groupby('id_student')['event_type'].apply(set).reset_index()
    
    # Filter: Must have 'submission' AND must have 'forum' (response)
    # If a student has submission but no forum, they are excluded.
    valid_students = student_events[
        student_events['event_type'].apply(lambda x: 'submission' in x and 'forum' in x)
    ]['id_student']
    
    initial_count = len(merged_df)
    merged_df = merged_df[merged_df['id_student'].isin(valid_students)]
    excluded_no_response = initial_count - len(merged_df)
    exclusion_counts["no_submission_response"] = excluded_no_response
    info(f"Excluded {excluded_no_response} learners who had submissions but no forum interactions (response)")
    
    # 5. Apply minimum learner filter per course
    merged_df = apply_min_learner_filter(merged_df, min_learners=50)
    exclusion_counts["small_courses"] = initial_count - len(merged_df) # Approximate for log, actual is records removed
    
    # 6. Final aggregation for learners_raw
    # We need one row per learner with their final result and presence of events
    # The task requires: "final grade", "completion status", "feedback interval" (though interval calc is T023)
    # For T017, we just need to ensure the data exists and is filtered correctly.
    
    # Create a summary per learner
    learner_summary = merged_df.groupby(['id_student', 'code_module', 'code_presentation']).agg({
        'final_result': 'first',
        'event_type': lambda x: list(x) # Keep event types to verify
    }).reset_index()
    
    # 7. Verification: Assert count >= 10,000
    if len(learner_summary) < 10000:
        error(f"Verification failed: Only {len(learner_summary)} records found. Expected >= 10,000.")
        sys.exit(1)
    
    exclusion_counts["final_count"] = len(learner_summary)
    
    # 8. Save artifacts
    output_path = processed_dir / "learners_raw.csv"
    log_path = processed_dir / "exclusion_log.txt"
    
    save_filtered_data(learner_summary, output_path, log_path, exclusion_counts)
    
    info(f"Preprocessing complete. {len(learner_summary)} learners processed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())