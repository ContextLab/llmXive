"""
Unit test to verify annotation coverage and validity.

Tests that:
- N=500 rows exist in the annotated CSV
- All rows have valid labels (High-Confidence or Ambiguous)
- No missing labels
- Coverage is >= 95% (allowing for early exit)
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

ANNOTATED_CSV_PATH = "data/annotated_turns.csv"
VALID_LABELS = {"High-Confidence", "Ambiguous"}
TARGET_COUNT = 500
MIN_COVERAGE = 0.95  # 95%

@pytest.fixture
def annotated_df():
    """Load the annotated CSV for testing."""
    if not os.path.exists(ANNOTATED_CSV_PATH):
        pytest.skip(f"Annotated CSV not found at {ANNOTATED_CSV_PATH}. Run annotate.py first.")
    
    return pd.read_csv(ANNOTATED_CSV_PATH)

def test_annotated_file_exists():
    """Test that the annotated CSV file exists."""
    assert os.path.exists(ANNOTATED_CSV_PATH), f"Annotated CSV not found at {ANNOTATED_CSV_PATH}"

def test_annotation_count(annotated_df):
    """Test that we have the target number of annotated rows (or close to it)."""
    count = len(annotated_df)
    
    # Allow for early exit (user quit before completing all 500)
    # But we expect at least 95% of the target if annotation was completed
    min_expected = int(TARGET_COUNT * MIN_COVERAGE)
    
    assert count >= min_expected, (
        f"Annotation count ({count}) is below minimum expected ({min_expected}). "
        f"Expected at least {min_expected} rows for {MIN_COVERAGE*100}% coverage of {TARGET_COUNT}."
    )

def test_required_columns_present(annotated_df):
    """Test that all required columns are present."""
    required_columns = ['query', 'ground_truth_intent', 'complexity_score']
    missing_columns = set(required_columns) - set(annotated_df.columns)
    
    assert not missing_columns, f"Missing required columns: {missing_columns}"

def test_no_missing_labels(annotated_df):
    """Test that there are no missing labels in the ground_truth_intent column."""
    null_labels = annotated_df['ground_truth_intent'].isna().sum()
    
    assert null_labels == 0, (
        f"Found {null_labels} missing labels in 'ground_truth_intent' column. "
        "All rows must have a valid label."
    )

def test_valid_labels_only(annotated_df):
    """Test that all labels are valid (High-Confidence or Ambiguous)."""
    invalid_labels = set(annotated_df['ground_truth_intent'].unique()) - VALID_LABELS
    
    assert not invalid_labels, (
        f"Found invalid labels: {invalid_labels}. "
        f"Only valid labels are: {VALID_LABELS}"
    )

def test_label_distribution(annotated_df):
    """Test that we have a reasonable distribution of labels."""
    label_counts = annotated_df['ground_truth_intent'].value_counts()
    
    # Ensure we have at least some of each label type
    assert 'High-Confidence' in label_counts.index, "No 'High-Confidence' labels found"
    assert 'Ambiguous' in label_counts.index, "No 'Ambiguous' labels found"
    
    # Log the distribution for debugging
    print(f"\nLabel distribution:\n{label_counts}")

def test_query_column_not_empty(annotated_df):
    """Test that the query column has no empty values."""
    empty_queries = annotated_df['query'].isna().sum() + (annotated_df['query'] == '').sum()
    
    assert empty_queries == 0, (
        f"Found {empty_queries} empty or NaN queries. "
        "All rows must have a valid query."
    )

def test_coverage_threshold_met(annotated_df):
    """Test that coverage threshold (>= 95%) is met."""
    actual_coverage = len(annotated_df) / TARGET_COUNT
    
    assert actual_coverage >= MIN_COVERAGE, (
        f"Coverage ({actual_coverage:.2%}) is below threshold ({MIN_COVERAGE:.2%}). "
        f"Need at least {int(TARGET_COUNT * MIN_COVERAGE)} rows, have {len(annotated_df)}."
    )