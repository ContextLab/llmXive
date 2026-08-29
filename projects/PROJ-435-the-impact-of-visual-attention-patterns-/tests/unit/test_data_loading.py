import pytest
import pandas as pd
import numpy as np
import hashlib
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import from the project's utility module
from code.utils.data_loading import compute_sha256, verify_checksum, validate_eye_tracking_schema

def test_compute_sha256():
    # Test SHA256 computation for a string
    data = b"Hello, World!"
    expected_hash = hashlib.sha256(data).hexdigest()
    actual_hash = compute_sha256(data)
    assert actual_hash == expected_hash

def test_compute_sha256_file(tmp_path):
    # Test SHA256 computation for a file
    test_file = tmp_path / "test.txt"
    test_content = b"Test content for hashing"
    test_file.write_bytes(test_content)
    
    expected_hash = hashlib.sha256(test_content).hexdigest()
    actual_hash = compute_sha256(test_file.read_bytes())
    assert actual_hash == expected_hash

def test_verify_checksum_match(tmp_path):
    # Test checksum verification with matching hashes
    test_file = tmp_path / "test.txt"
    test_content = b"Content to verify"
    test_file.write_bytes(test_content)
    
    computed_hash = compute_sha256(test_content)
    assert verify_checksum(test_content, computed_hash) is True

def test_verify_checksum_mismatch(tmp_path):
    # Test checksum verification with mismatched hashes
    test_content = b"Content to verify"
    wrong_hash = "0" * 64  # Invalid hash
    
    assert verify_checksum(test_content, wrong_hash) is False

def test_validate_eye_tracking_schema_valid():
    # Test schema validation with valid columns
    df = pd.DataFrame({
        'headline_text': ['Headline 1', 'Headline 2'],
        'belief_rating': [5, 4],
        'cognitive_reflection_score': [2, 1],
        'fixation_duration': [100, 150]
    })
    
    required_columns = ['headline_text', 'belief_rating', 'cognitive_reflection_score', 'fixation_duration']
    is_valid, missing = validate_eye_tracking_schema(df, required_columns)
    assert is_valid is True
    assert len(missing) == 0

def test_validate_eye_tracking_schema_missing_columns():
    # Test schema validation with missing columns
    df = pd.DataFrame({
        'headline_text': ['Headline 1', 'Headline 2'],
        'belief_rating': [5, 4]
    })
    
    required_columns = ['headline_text', 'belief_rating', 'cognitive_reflection_score', 'fixation_duration']
    is_valid, missing = validate_eye_tracking_schema(df, required_columns)
    assert is_valid is False
    assert 'cognitive_reflection_score' in missing
    assert 'fixation_duration' in missing
