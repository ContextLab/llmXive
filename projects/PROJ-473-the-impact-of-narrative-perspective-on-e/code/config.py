import os
import numpy as np
import logging

def get_config():
    """
    Get project configuration including paths, seeds, and hyperparameters.
    
    Returns:
        Dictionary containing configuration values
    """
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Define primary matching threshold for T025
    PRIMARY_MATCHING_THRESHOLD = 0.30
    
    # Define paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
    ARTIFACTS_DIR = os.path.join(DATA_DIR, "artifacts")
    CODE_DIR = os.path.join(BASE_DIR, "code")
    
    # Define specific file paths
    GOLD_STANDARD_ANNOTATIONS_PATH = os.path.join(RAW_DATA_DIR, "gold_standard_annotations.csv")
    GUTENBERG_STORIES_DIR = os.path.join(RAW_DATA_DIR, "gutenberg_stories")
    PERSPECTIVE_FEATURES_PATH = os.path.join(PROCESSED_DATA_DIR, "perspective_features.json")
    READER_RESPONSE_PATH = os.path.join(PROCESSED_DATA_DIR, "reader_response.csv")
    ALIGNED_DATASET_PATH = os.path.join(PROCESSED_DATA_DIR, "aligned_dataset.csv")
    ANALYSIS_RESULTS_PATH = os.path.join(PROCESSED_DATA_DIR, "analysis_results.json")
    SENSITIVITY_REPORT_PATH = os.path.join(PROCESSED_DATA_DIR, "sensitivity_report.json")
    MATCHING_RESULTS_PATH = os.path.join(PROCESSED_DATA_DIR, "matching_results.json")
    THRESHOLDS_PATH = os.path.join(PROCESSED_DATA_DIR, "thresholds.json")
    
    # Define hyperparameters
    MIN_WORD_COUNT = 50
    MAX_STORY_LENGTH = 10000  # characters
    
    return {
        'np_random_seed': 42,
        'PRIMARY_MATCHING_THRESHOLD': PRIMARY_MATCHING_THRESHOLD,
        'BASE_DIR': BASE_DIR,
        'DATA_DIR': DATA_DIR,
        'RAW_DATA_DIR': RAW_DATA_DIR,
        'PROCESSED_DATA_DIR': PROCESSED_DATA_DIR,
        'ARTIFACTS_DIR': ARTIFACTS_DIR,
        'CODE_DIR': CODE_DIR,
        'GOLD_STANDARD_ANNOTATIONS_PATH': GOLD_STANDARD_ANNOTATIONS_PATH,
        'GUTENBERG_STORIES_DIR': GUTENBERG_STORIES_DIR,
        'PERSPECTIVE_FEATURES_PATH': PERSPECTIVE_FEATURES_PATH,
        'READER_RESPONSE_PATH': READER_RESPONSE_PATH,
        'ALIGNED_DATASET_PATH': ALIGNED_DATASET_PATH,
        'ANALYSIS_RESULTS_PATH': ANALYSIS_RESULTS_PATH,
        'SENSITIVITY_REPORT_PATH': SENSITIVITY_REPORT_PATH,
        'MATCHING_RESULTS_PATH': MATCHING_RESULTS_PATH,
        'THRESHOLDS_PATH': THRESHOLDS_PATH,
        'MIN_WORD_COUNT': MIN_WORD_COUNT,
        'MAX_STORY_LENGTH': MAX_STORY_LENGTH,
    }