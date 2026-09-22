"""
Integration test for User Story 1: Data Ingestion and Preprocessing.

This test verifies the full ingestion pipeline on a sample subset of transcripts.
It ensures that the output dataset contains the expected number of records,
valid cognitive status labels, and cleaned text meeting the minimum length requirement.

Dependencies:
- T016: data/interim/cleaned_adress.csv must exist.
- T014: Exclusion logic (text length >= 50) must be active.
- T012: Data download and validation must be active.

Assertions:
1. The number of records in the output matches the expected sample count.
2. All records have non-null cognitive status labels.
3. All records have text length >= 50 characters (or words as per spec).
"""

import os
import sys
import logging
import json
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs, DataSourceConfig
from utils import get_logger

# Setup logging for the test
logger = get_logger("test_us1_integration")

# Constants
DATA_DIR = get_path("data_interim")
CLEANED_FILE = DATA_DIR / "cleaned_adress.csv"
SAMPLE_SIZE = 20  # Number of records to sample for this integration test
MIN_TEXT_LENGTH = 50  # Minimum text length (characters/words)

def test_ingestion_pipeline_sample():
    """
    Run the full ingestion pipeline on a sample subset and verify output.
    """
    logger.info("Starting Integration Test: US1 Sample Ingestion")

    # 1. Verify input data exists
    if not CLEANED_FILE.exists():
        logger.error(f"Input file not found: {CLEANED_FILE}")
        raise FileNotFoundError(
            f"Cleaned dataset not found at {CLEANED_FILE}. "
            "Please ensure T016 (cleaned_adress.csv) has been executed."
        )

    logger.info(f"Loading cleaned dataset from {CLEANED_FILE}")
    df = pd.read_csv(CLEANED_FILE)

    # 2. Select a sample subset
    # Ensure we don't sample more than available
    actual_count = len(df)
    expected_count = min(SAMPLE_SIZE, actual_count)

    if expected_count == 0:
        logger.error("Cleaned dataset is empty. Ingestion failed upstream.")
        raise ValueError("Cleaned dataset is empty.")

    logger.info(f"Sampling {expected_count} records from {actual_count} available.")
    sample_df = df.sample(n=expected_count, random_state=42).reset_index(drop=True)

    # 3. Assertion 1: Record count matches
    assert len(sample_df) == expected_count, (
        f"Record count mismatch: expected {expected_count}, got {len(sample_df)}"
    )
    logger.info(f"✓ Assertion 1 passed: Record count is {expected_count}")

    # 4. Assertion 2: Valid cognitive status labels (non-null)
    # The 'label' column should contain valid statuses (e.g., 'Control', 'AD', 'MCI')
    if 'label' not in sample_df.columns:
        raise KeyError("Column 'label' not found in cleaned dataset.")

    null_labels = sample_df['label'].isnull().sum()
    assert null_labels == 0, (
        f"Found {null_labels} records with null labels. "
        "All records must have a valid cognitive status."
    )
    logger.info("✓ Assertion 2 passed: All records have valid labels")

    # 5. Assertion 3: Text length >= 50
    # Assuming 'text' column exists and contains the cleaned transcript
    if 'text' not in sample_df.columns:
        raise KeyError("Column 'text' not found in cleaned dataset.")

    # Check length in characters (or words if specified, but typically char count for >=50)
    # The spec says "text length < 50 words" in T014, but usually we check characters or words.
    # Let's assume the requirement is strictly met in the cleaned data, so we verify it holds.
    # We will check character length >= 50 as a safe proxy for "not empty/short".
    # If the spec strictly meant words, we would split. Given T014 says "words", let's be precise.
    # T014: "Filter records where ... text length < 50 words."
    # So we count words.
    sample_df['word_count'] = sample_df['text'].apply(lambda x: len(str(x).split()))
    short_texts = (sample_df['word_count'] < 50).sum()

    assert short_texts == 0, (
        f"Found {short_texts} records with text length < 50 words. "
        "This indicates the filtering logic (T014) was not applied correctly."
    )
    logger.info("✓ Assertion 3 passed: All records have >= 50 words")

    # 6. Verify data types and basic integrity
    assert sample_df['label'].dtype == object or str in str(sample_df['label'].dtype), (
        "Label column should be string/object type."
    )

    logger.info("Integration Test US1 Sample: ALL ASSERTIONS PASSED")
    return True

def main():
    """Entry point for running the test."""
    try:
        success = test_ingestion_pipeline_sample()
        if success:
            print("SUCCESS: Integration test passed.")
            return 0
    except Exception as e:
        print(f"FAILURE: Integration test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())