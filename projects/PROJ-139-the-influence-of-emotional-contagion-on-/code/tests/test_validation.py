import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from code.data.validation import (
    check_ground_truth_availability,
    classify_thread,
    validate_and_classify,
    save_validated_dataset,
    save_exclusions_log,
    check_valid_thread_threshold_with_total,
    generate_validity_status_report
)

# Sample data for testing
def sample_valid_thread_stackexchange():
    return {
        'thread_id': 'SE_001',
        'source': 'stackexchange',
        'accepted_answer_id': 'ans_123',
        'title': 'How to fix Python error',
        'body': 'I am getting an error...',
        'replies': []
    }

def sample_invalid_thread_stackexchange():
    return {
        'thread_id': 'SE_002',
        'source': 'stackexchange',
        'accepted_answer_id': None,
        'title': 'Question without answer',
        'body': 'I have a question...',
        'replies': []
    }

def sample_valid_thread_reddit():
    return {
        'thread_id': 'RD_001',
        'source': 'reddit',
        'replies': [
            {'id': 'r1', 'body': 'This is the accepted solution.', 'upvotes': 100},
            {'id': 'r2', 'body': 'Try this.', 'upvotes': 50}
        ]
    }

def sample_invalid_thread_reddit():
    return {
        'thread_id': 'RD_002',
        'source': 'reddit',
        'replies': [
            {'id': 'r1', 'body': 'I don\'t know.', 'upvotes': 10},
            {'id': 'r2', 'body': 'Maybe.', 'upvotes': 5}
        ]
    }

def sample_thread_missing_source():
    return {
        'thread_id': 'UNKNOWN_001',
        'source': 'unknown',
        'replies': []
    }

def test_check_ground_truth_valid_stackexchange():
    thread = sample_valid_thread_stackexchange()
    assert check_ground_truth_availability(thread) is True

def test_check_ground_truth_missing_label_stackexchange():
    thread = sample_invalid_thread_stackexchange()
    assert check_ground_truth_availability(thread) is False

def test_check_ground_truth_valid_reddit():
    thread = sample_valid_thread_reddit()
    assert check_ground_truth_availability(thread) is True

def test_check_ground_truth_missing_source():
    thread = sample_thread_missing_source()
    assert check_ground_truth_availability(thread) is False

def test_classify_thread_valid():
    thread = sample_valid_thread_stackexchange()
    classification, reason = classify_thread(thread)
    assert classification == 'valid'
    assert reason is None

def test_classify_thread_invalid():
    thread = sample_invalid_thread_stackexchange()
    classification, reason = classify_thread(thread)
    assert classification == 'excluded'
    assert reason == 'ground_truth_missing'

def test_validate_and_classify():
    data = [
        sample_valid_thread_stackexchange(),
        sample_invalid_thread_stackexchange(),
        sample_valid_thread_reddit(),
        sample_invalid_thread_reddit()
    ]
    df = pd.DataFrame(data)
    
    valid_df, excluded_df = validate_and_classify(df)
    
    assert len(valid_df) == 2
    assert len(excluded_df) == 2
    assert valid_df.iloc[0]['thread_id'] == 'SE_001'
    assert valid_df.iloc[1]['thread_id'] == 'RD_001'
    assert excluded_df.iloc[0]['thread_id'] == 'SE_002'
    assert excluded_df.iloc[1]['thread_id'] == 'RD_002'

def test_save_validated_dataset():
    data = [sample_valid_thread_stackexchange()]
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        save_validated_dataset(df, temp_path)
        assert os.path.exists(temp_path)
        loaded_df = pd.read_csv(temp_path)
        assert len(loaded_df) == 1
        assert loaded_df.iloc[0]['thread_id'] == 'SE_001'
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_save_exclusions_log():
    data = [sample_invalid_thread_stackexchange()]
    df = pd.DataFrame(data)
    df['exclusion_reason'] = 'ground_truth_missing'
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_path = f.name
    
    try:
        save_exclusions_log(df, temp_path)
        assert os.path.exists(temp_path)
        loaded_df = pd.read_csv(temp_path)
        assert len(loaded_df) == 1
        assert loaded_df.iloc[0]['exclusion_reason'] == 'ground_truth_missing'
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_check_valid_thread_threshold_with_total_pass():
    result = check_valid_thread_threshold_with_total(total_threads=100, valid_threads=40, threshold=0.30)
    assert result['valid_thread_percentage'] == 40.0
    assert result['status'] == 'pass'
    assert result['total_threads'] == 100
    assert result['valid_threads'] == 40

def test_check_valid_thread_threshold_with_total_fail():
    result = check_valid_thread_threshold_with_total(total_threads=100, valid_threads=20, threshold=0.30)
    assert result['valid_thread_percentage'] == 20.0
    assert result['status'] == 'fail'
    assert result['total_threads'] == 100
    assert result['valid_threads'] == 20

def test_check_valid_thread_threshold_with_total_zero_total():
    result = check_valid_thread_threshold_with_total(total_threads=0, valid_threads=0, threshold=0.30)
    assert result['valid_thread_percentage'] == 0.0
    assert result['status'] == 'fail'

def test_generate_validity_status_report():
    data = [sample_valid_thread_stackexchange(), sample_invalid_thread_stackexchange()]
    valid_df = pd.DataFrame([data[0]])
    total_threads = 2
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        generate_validity_status_report(valid_df, total_threads, temp_path, threshold=0.30)
        assert os.path.exists(temp_path)
        
        with open(temp_path, 'r') as f:
            report = json.load(f)
        
        assert report['valid_thread_percentage'] == 50.0
        assert report['status'] == 'pass'
        assert report['threshold'] == 30.0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_empty_dataframe_handling():
    df = pd.DataFrame()
    valid_df, excluded_df = validate_and_classify(df)
    assert len(valid_df) == 0
    assert len(excluded_df) == 0

def test_generate_failure_report_pass():
    # Simulate a case where validation passes
    result = check_valid_thread_threshold_with_total(100, 50, 0.30)
    assert result['status'] == 'pass'

def test_generate_failure_report_fail():
    # Simulate a case where validation fails
    result = check_valid_thread_threshold_with_total(100, 20, 0.30)
    assert result['status'] == 'fail'

def test_generate_failure_report_edge_case():
    # Edge case: exactly at threshold
    result = check_valid_thread_threshold_with_total(100, 30, 0.30)
    assert result['status'] == 'pass'
    assert result['valid_thread_percentage'] == 30.0