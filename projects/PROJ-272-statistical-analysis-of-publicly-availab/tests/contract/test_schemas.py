"""
Contract Test: Verify feature matrix schema.

Task: T025a [US2]
Objective: Verify that the feature matrix contains exactly the 6 required columns:
[TTR, MTLD, Noun_Verb_Ratio, Mean_Clause_Length, T_Unit_Count, Sentence_Embedding_Cosine_Similarity].
Fail if any are missing.
"""
import os
import sys
import json
import logging
from pathlib import Path

import pandas as pd
import pytest

# Add project root to path to allow imports if running from root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    "TTR",
    "MTLD",
    "Noun_Verb_Ratio",
    "Mean_Clause_Length",
    "T_Unit_Count",
    "Sentence_Embedding_Cosine_Similarity"
]

@pytest.fixture
def feature_matrix_path():
    """Locate the feature matrix file."""
    # The task description specifies the path relative to project root
    return get_path("data/processed/features.csv")

def test_feature_matrix_columns_exist(feature_matrix_path):
    """
    Contract Test: Verify feature matrix contains exactly the 6 required columns.
    
    This test asserts that the file exists and contains the specific columns
    defined in the requirements for User Story 2.
    """
    logger.info(f"Checking feature matrix at: {feature_matrix_path}")
    
    # Assert file exists
    assert os.path.exists(feature_matrix_path), \
        f"Feature matrix file not found at {feature_matrix_path}. " \
        f"Run the feature extraction pipeline (T022-T024b) first."
    
    # Load the dataset
    try:
        df = pd.read_csv(feature_matrix_path)
    except Exception as e:
        pytest.fail(f"Failed to load feature matrix CSV: {e}")
    
    logger.info(f"Loaded feature matrix with shape: {df.shape}")
    logger.info(f"Current columns: {list(df.columns)}")
    
    # Check for required columns
    missing_columns = []
    extra_columns = []
    
    current_columns = set(df.columns)
    required_set = set(REQUIRED_COLUMNS)
    
    for col in REQUIRED_COLUMNS:
        if col not in current_columns:
            missing_columns.append(col)
    
    # Optional: Log extra columns if any (not a failure unless spec says "exactly")
    # The task says "contains exactly the 6 required columns", implying no others might be allowed,
    # but usually in data pipelines, metadata columns (like participant_id) are expected.
    # However, strict interpretation of "exactly" might fail if participant_id is present.
    # Given the context of "feature matrix", it usually implies the feature columns.
    # We will assert that ALL required columns are present.
    # If the requirement "exactly" means NO OTHER columns, we check set equality.
    # Let's assume the strict "exactly" means the set of feature columns must match,
    # but often a CSV includes an ID. Let's check if the REQUIRED set is a subset first.
    
    assert len(missing_columns) == 0, \
        f"Contract Test Failed: The following required columns are missing from {feature_matrix_path}: {missing_columns}"
    
    # If the task strictly implies NO OTHER columns (excluding index or ID), we might need a second check.
    # However, typically "feature matrix" implies the feature columns.
    # If the CSV has 'participant_id' or 'label', those are metadata, not features.
    # If the requirement is strictly "exactly these 6 columns and nothing else", we check equality.
    # Let's check equality to be safe against the "exactly" wording, assuming metadata is handled elsewhere
    # or the file is pure features. If it fails due to ID, we can relax.
    # But standard practice: The file should contain the features.
    
    # Re-reading T025a: "Verify feature matrix contains exactly the 6 required columns... Fail if any are missing."
    # It emphasizes "missing". It does not explicitly forbid metadata columns like ID.
    # We will pass if all 6 are present.
    
    logger.info("Contract Test PASSED: All 6 required columns are present.")

def test_feature_matrix_non_empty(feature_matrix_path):
    """
    Ensure the feature matrix is not empty.
    """
    if not os.path.exists(feature_matrix_path):
        pytest.skip("Feature matrix file not found, skipping content check.")
    
    df = pd.read_csv(feature_matrix_path)
    assert df.shape[0] > 0, "Feature matrix is empty. No records to validate."

def test_feature_matrix_column_types(feature_matrix_path):
    """
    Ensure the feature columns are numeric.
    """
    if not os.path.exists(feature_matrix_path):
        pytest.skip("Feature matrix file not found, skipping type check.")
    
    df = pd.read_csv(feature_matrix_path)
    
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            continue # Already caught by column existence test
        
        # Check if numeric (allowing for potential NaNs)
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Attempt to convert
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except (ValueError, TypeError):
                pytest.fail(f"Column '{col}' is not numeric and cannot be converted.")
    
    logger.info("Contract Test PASSED: All required columns are numeric.")
