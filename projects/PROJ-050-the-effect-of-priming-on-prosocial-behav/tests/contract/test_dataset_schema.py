"""
Contract test for dataset schema validation (T010).
Verifies that the output of T015 (anonymized.csv) adheres to the expected schema.
"""
import pytest
import pandas as pd
from pathlib import Path

# Determine project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

@pytest.fixture
def anonymized_df():
    """Load the anonymized dataset if it exists."""
    csv_path = DATA_PROCESSED_DIR / "anonymized.csv"
    if not csv_path.exists():
        pytest.skip(f"anonymized.csv not found at {csv_path}. Run T015 (ingest pipeline) first.")
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        pytest.fail(f"Failed to load anonymized.csv: {e}")

def test_schema_columns(anonymized_df):
    """Verify required columns exist."""
    required_columns = [
        'id', 'subreddit', 'body', 'thread_type', 'user_id', 'thread_age_days'
    ]
    missing = [col for col in required_columns if col not in anonymized_df.columns]
    assert not missing, f"Missing required columns: {missing}"

def test_thread_type_values(anonymized_df):
    """Verify thread_type is binary (Prime/Control)."""
    valid_types = {'Prime', 'Control'}
    actual_types = set(anonymized_df['thread_type'].unique())
    invalid = actual_types - valid_types
    assert not invalid, f"Invalid thread_type values found: {invalid}"

def test_user_id_format(anonymized_df):
    """Verify user_id is a SHA-256 hash (64 hex chars)."""
    # Skip if empty
    if anonymized_df['user_id'].empty:
        pytest.skip("user_id column is empty.")
    
    sample_ids = anonymized_df['user_id'].dropna().head(10)
    for uid in sample_ids:
        assert isinstance(uid, str), f"user_id must be string, got {type(uid)}"
        assert len(uid) == 64, f"user_id must be 64 chars (SHA-256), got {len(uid)}"
        try:
            int(uid, 16) # Check if hex
        except ValueError:
            pytest.fail(f"user_id '{uid}' is not a valid hex string")

def test_no_plaintext_author(anonymized_df):
    """Verify 'author' column does not exist."""
    assert 'author' not in anonymized_df.columns, "Raw 'author' column must be removed."

def test_no_plaintext_timestamp(anonymized_df):
    """Verify 'created_utc' column does not exist."""
    assert 'created_utc' not in anonymized_df.columns, "Raw 'created_utc' column must be removed."

def test_group_counts(anonymized_df):
    """Verify at least MIN_GROUP_SIZE per group (4000)."""
    MIN_GROUP_SIZE = 4000
    prime_count = (anonymized_df['thread_type'] == 'Prime').sum()
    control_count = (anonymized_df['thread_type'] == 'Control').sum()
    
    assert prime_count >= MIN_GROUP_SIZE, f"Prime group too small: {prime_count} < {MIN_GROUP_SIZE}"
    assert control_count >= MIN_GROUP_SIZE, f"Control group too small: {control_count} < {MIN_GROUP_SIZE}"

def test_subreddit_count(anonymized_df):
    """Verify at least 3 subreddits."""
    assert anonymized_df['subreddit'].nunique() >= 3, "Must have at least 3 subreddits."
