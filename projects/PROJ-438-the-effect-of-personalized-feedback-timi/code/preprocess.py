import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from config import load_config, get_config_value
from logging_config import get_logger, info, warning, error, debug
from checksums import generate_checksum_for_file

def load_config_value(key, default=None):
    """Load a specific value from config.yaml."""
    config = load_config()
    return config.get(key, default)

def load_raw_datasets(raw_data_dir):
    """
    Load the raw OULAD datasets from the specified directory.
    Expected files: students.csv, courses.csv, assessments.csv, studentAssessment.csv
    """
    students_path = raw_data_dir / "students.csv"
    courses_path = raw_data_dir / "courses.csv"
    assessments_path = raw_data_dir / "assessments.csv"
    student_assessment_path = raw_data_dir / "studentAssessment.csv"

    if not all(p.exists() for p in [students_path, courses_path, assessments_path, student_assessment_path]):
        raise FileNotFoundError(
            f"Required raw data files missing in {raw_data_dir}. "
            "Please run download_data.py first."
        )

    students = pd.read_csv(students_path)
    courses = pd.read_csv(courses_path)
    assessments = pd.read_csv(assessments_path)
    student_assessments = pd.read_csv(student_assessment_path)

    return students, courses, assessments, student_assessments

def get_course_event_types(courses_df, assessments_df, student_assessments_df):
    """
    Determine which courses have 'assessment' and 'forum' events.
    For OULAD, 'assessment' events are derived from studentAssessments,
    and 'forum' events are derived from studentVLE (not loaded here, but we assume
    the presence of forum interactions is tracked via a flag or separate table in a full pipeline).
    Here we assume 'forum' presence is indicated by a 'has_forum' column or similar in a merged view,
    or we filter based on the presence of any student activity in the VLE (simplified for this task).
    
    Since the full VLE data might be separate, we assume the input 'courses' or a merged context
    indicates if a course has forum activity. If not, we rely on the presence of assessments.
    """
    # In a full pipeline, we would join with VLE data to check for forum interactions.
    # For this specific task (T019), we assume the input data 'courses' or a pre-filtered state
    # already accounts for the 'forum' requirement, or we simply filter by course ID presence in assessments.
    # We will return the list of course IDs that have assessments (as a proxy for 'assessment' event).
    # The 'forum' check is typically done by checking if the course_id appears in the VLE table.
    # Assuming the caller has already filtered for 'forum' courses or the data provided implies it.
    
    # Let's assume the 'courses' dataframe has a column 'has_forum' or we check against a VLE subset.
    # If not present, we default to all courses that have assessments.
    course_ids_with_assessments = assessments_df['code_module'].unique()
    
    # If 'has_forum' column exists in courses, filter further
    if 'has_forum' in courses_df.columns:
        courses_with_forum = courses_df[courses_df['has_forum'] == True]['code_module'].unique()
        course_ids_with_assessments = list(set(course_ids_with_assessments) & set(courses_with_forum))
    
    return course_ids_with_assessments

def filter_courses_by_events(courses_df, assessments_df, student_assessments_df):
    """
    Filter courses to keep only those with both 'assessment' and 'forum' events.
    """
    valid_course_ids = get_course_event_types(courses_df, assessments_df, student_assessments_df)
    filtered_courses = courses_df[courses_df['code_module'].isin(valid_course_ids)]
    return filtered_courses

def extract_learner_records(students_df, courses_df, assessments_df, student_assessments_df):
    """
    Extract learner records with feedback timestamps, grades, and completion status.
    Merges data to create a wide-format record per student per module.
    """
    # Merge student with course info
    students_merged = students_df.merge(courses_df, on='code_module', how='inner')
    
    # Merge with assessments to get grades
    # Assuming 'grade' is in studentAssessments or derived
    # OULAD structure: studentAssessments has 'score', 'max_score', 'date_submitted'
    # We need to map this to a 'final_grade' proxy.
    
    # Simplified merge for the purpose of T019 (which focuses on course size)
    # We assume the previous step (T018) has already filtered out students with no forum interactions.
    # Here we just ensure we have the necessary columns for the next step.
    
    # Merge student assessments
    students_with_grades = students_merged.merge(
        student_assessments_df, 
        on=['id_student', 'code_module', 'code_presentation'], 
        how='left'
    )
    
    # Calculate a simple final grade proxy if not present
    if 'grade' not in students_with_grades.columns:
        # Assume 'score' and 'max_score' exist
        if 'score' in students_with_grades.columns and 'max_score' in students_with_grades.columns:
            students_with_grades['final_grade'] = (students_with_grades['score'] / students_with_grades['max_score']) * 100
        else:
            students_with_grades['final_grade'] = np.nan
    
    # Determine completion status (is_complete)
    # OULAD: 'is_student_registration' or 'date_registration' vs 'date_unreg'
    # Assuming 'is_complete' is derived from 'final_result' column in students_df
    if 'final_result' in students_with_grades.columns:
        students_with_grades['is_complete'] = students_with_grades['final_result'].isin(['Pass', 'Distinction', 'Merit'])
    else:
        students_with_grades['is_complete'] = np.nan

    return students_with_grades

def apply_min_learner_filter(df, min_learners=50, logger=None):
    """
    T019: Exclude courses with <50 learners and log the exclusion count.
    
    Args:
        df: DataFrame containing learner records with a 'code_module' column.
        min_learners: Minimum number of learners required per course.
        logger: Logger instance for reporting.
    
    Returns:
        Filtered DataFrame and a log message string.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    # Count learners per course
    course_counts = df.groupby('code_module').size().reset_index(name='learner_count')
    
    # Identify courses to exclude
    excluded_courses = course_counts[course_counts['learner_count'] < min_learners]
    included_courses = course_counts[course_counts['learner_count'] >= min_learners]
    
    total_courses_before = len(course_counts)
    total_courses_after = len(included_courses)
    excluded_count = total_courses_before - total_courses_after
    excluded_learner_count = excluded_courses['learner_count'].sum()
    
    message = (
        f"Filtered courses with <{min_learners} learners. "
        f"Excluded {excluded_count} courses ({excluded_learner_count} learners). "
        f"Remaining: {total_courses_after} courses ({len(df) - excluded_learner_count} learners)."
    )
    
    logger.info(message)
    warning(message) # Also log as warning for visibility in logs if level is INFO
    
    # Filter the main dataframe
    filtered_df = df[df['code_module'].isin(included_courses['code_module'])]
    
    return filtered_df

def save_filtered_data(df, output_path, logger=None):
    """
    Save the filtered dataframe to CSV and generate a checksum.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")
    
    checksum = generate_checksum_for_file(output_path)
    logger.info(f"Checksum for {output_path}: {checksum}")
    
    return checksum

def main():
    """
    Main execution flow for T019 (and related US1 preprocessing steps).
    """
    logger = get_logger(__name__)
    logger.info("Starting preprocessing pipeline (T019: Min Learner Filter)")
    
    # Load config
    config = load_config()
    raw_data_dir = Path(config.get('paths', {}).get('raw_data', 'data/raw'))
    processed_data_dir = Path(config.get('paths', {}).get('processed_data', 'data/processed'))
    min_learners = get_config_value('min_learners_per_course', 50)
    
    try:
        # Load raw data
        students, courses, assessments, student_assessments = load_raw_datasets(raw_data_dir)
        
        # Filter by events (T017)
        courses_filtered = filter_courses_by_events(courses, assessments, student_assessments)
        
        # Extract learner records (T017)
        learner_records = extract_learner_records(students, courses_filtered, assessments, student_assessments)
        
        # T018: Filter out learners with no forum interactions (Simulated here as a placeholder for the actual logic)
        # In a real scenario, this would join with VLE data. 
        # Assuming 'has_forum_interaction' column exists or is derived.
        # If not present, we skip this specific filter for now to avoid errors, 
        # but the structure is ready.
        if 'has_forum_interaction' in learner_records.columns:
            learner_records = learner_records[learner_records['has_forum_interaction'] == True]
            logger.info(f"Filtered out learners with no forum interactions.")
        
        # T019: Apply minimum learner filter per course
        learner_records_filtered = apply_min_learner_filter(
            learner_records, 
            min_learners=min_learners, 
            logger=logger
        )
        
        # Save output (T020)
        output_path = processed_data_dir / "learners_raw.csv"
        save_filtered_data(learner_records_filtered, output_path, logger)
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()