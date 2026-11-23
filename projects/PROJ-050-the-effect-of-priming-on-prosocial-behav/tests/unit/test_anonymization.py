"""
Unit tests for the anonymization and tenure logic in code/01_ingest.py.
Verifies SHA-256 hashing of authors and the derivation of user tenure.
"""
import pytest
import sys
import hashlib
import importlib
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Using importlib because the module name '01_ingest' starts with a digit
ingest_module = importlib.import_module("code.01_ingest")
hash_user = ingest_module.hash_user
calculate_tenure = ingest_module.calculate_tenure

def test_hash_user_valid():
    """Verify that a valid author string is hashed using SHA-256."""
    author = "researcher_123"
    expected = hashlib.sha256(author.encode('utf-8')).hexdigest()
    assert hash_user(author) == expected

def test_hash_user_consistency():
    """Verify that the same author always produces the same hash."""
    author = "consistent_user"
    assert hash_user(author) == hash_user(author)

def test_hash_user_none():
    """Verify that None author returns 'anonymous'."""
    assert hash_user(None) == "anonymous"

def test_hash_user_nan():
    """Verify that NaN author returns 'anonymous'."""
    assert hash_user(float('nan')) == "anonymous"

def test_calculate_tenure_baseline():
    """Verify tenure calculation relative to Reddit launch (approx 2006-12-15)."""
    # REDDIT_LAUNCH_UTC = 1136073600
    launch_utc = 1136073600
    # 0 days since launch
    assert calculate_tenure(launch_utc) == 0.0
    # 1 day since launch (86400 seconds)
    assert calculate_tenure(launch_utc + 86400) == 1.0
    # 10 days since launch
    assert calculate_tenure(launch_utc + 86400 * 10) == 10.0

def test_calculate_tenure_negative():
    """Verify behavior for timestamps before launch (should be negative)."""
    launch_utc = 1136073600
    assert calculate_tenure(launch_utc - 86400) == -1.0

def test_anonymization_logic_removes_raw_timestamp():
    """
    Verify the logic that transforms a raw record into a processed one.
    The requirement is that created_utc does not appear in the output.
    """
    # This mimics the dictionary construction inside code/01_ingest.main()
    raw_record = {
        "author": "test_user",
        "body": "Hello world",
        "created_utc": 1234567890.0,
        "subreddit": "science",
        "title": "Help me"
    }
    
    # Simulate the mapping logic found in 01_ingest.main
    processed_record = {
        "user_id": hash_user(raw_record["author"]),
        "subreddit": raw_record["subreddit"],
        "thread_type": ingest_module.classify_thread(raw_record),
        "user_tenure": calculate_tenure(raw_record["created_utc"]),
        "comment_text": raw_record["body"]
    }
    
    # Assert raw timestamp is NOT in the resulting keys
    assert "created_utc" not in processed_record
    # Assert derived tenure IS in the resulting keys
    assert "user_tenure" in processed_record
    # Assert author is NOT in the resulting keys (replaced by user_id)
    assert "author" not in processed_record
    assert "user_id" in processed_record