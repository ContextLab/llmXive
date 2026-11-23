import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from data.extract import (
    load_downloaded_data,
    count_top_level_posts,
    extract_seed_posts,
    validate_metadata_completeness,
    run_extraction,
    save_exclusions_log
)

def test_extract_seed_posts():
    """Test that seed posts are correctly extracted."""
    thread = {
        'id': 't1',
        'children': [
            {'id': 'c1', 'author': 'u1', 'created_utc': 100, 'body': 'post1'},
            {'id': 'c2', 'author': 'u2', 'created_utc': 200, 'body': 'post2'},
            {'id': 'c3', 'author': 'u3', 'created_utc': 300, 'body': 'post3'},
            {'id': 'c4', 'author': 'u4', 'created_utc': 400, 'body': 'post4'}
        ]
    }
    seeds = extract_seed_posts(thread, n=3)
    assert len(seeds) == 3
    assert seeds[0]['id'] == 'c1'
    assert seeds[1]['id'] == 'c2'
    assert seeds[2]['id'] == 'c3'

def test_flag_insufficient_seeds():
    """Test that threads with insufficient seeds are identified."""
    thread = {
        'id': 't1',
        'children': [
            {'id': 'c1', 'author': 'u1', 'created_utc': 100, 'body': 'post1'},
            {'id': 'c2', 'author': 'u2', 'created_utc': 200, 'body': 'post2'}
        ]
    }
    count = count_top_level_posts(thread)
    assert count == 2
    assert count < 3

def test_metadata_completeness():
    """Test metadata completeness validation."""
    # Complete data
    complete_data = [
        {'id': 't1', 'author': 'u1', 'created_utc': 100, 'body': 'b1', 'children': [
            {'id': 'c1', 'author': 'u1', 'created_utc': 100, 'body': 'b1'}
        ]},
        {'id': 't2', 'author': 'u2', 'created_utc': 200, 'body': 'b2', 'children': [
            {'id': 'c2', 'author': 'u2', 'created_utc': 200, 'body': 'b2'}
        ]}
    ]
    report = validate_metadata_completeness(complete_data)
    assert report['completeness_percentage'] == 100.0
    assert report['status'] == 'pass'

    # Incomplete data (missing author in one thread)
    incomplete_data = [
        {'id': 't1', 'author': 'u1', 'created_utc': 100, 'body': 'b1', 'children': []},
        {'id': 't2', 'author': None, 'created_utc': 200, 'body': 'b2', 'children': []},
        {'id': 't3', 'author': 'u3', 'created_utc': 300, 'body': 'b3', 'children': []},
        {'id': 't4', 'author': 'u4', 'created_utc': 400, 'body': 'b4', 'children': []},
        {'id': 't5', 'author': 'u5', 'created_utc': 500, 'body': 'b5', 'children': []}
    ]
    # 4/5 = 80%
    report = validate_metadata_completeness(incomplete_data)
    assert report['completeness_percentage'] == 80.0
    assert report['status'] == 'fail'
    assert len(report['missing_fields']) == 1
    assert report['missing_fields'][0]['thread_id'] == 't2'

def test_run_extraction_integration(tmp_path):
    """Test the full extraction pipeline."""
    # Setup input data
    input_file = tmp_path / "raw.jsonl"
    exclusion_file = tmp_path / "exclusions.log"
    output_file = tmp_path / "output.csv"
    
    data = [
        {'id': 't1', 'children': [{'id': 'c1', 'author': 'u1', 'created_utc': 100, 'body': 'b1'}, {'id': 'c2', 'author': 'u2', 'created_utc': 200, 'body': 'b2'}, {'id': 'c3', 'author': 'u3', 'created_utc': 300, 'body': 'b3'}]},
        {'id': 't2', 'children': [{'id': 'c4', 'author': 'u4', 'created_utc': 400, 'body': 'b4'}, {'id': 'c5', 'author': 'u5', 'created_utc': 500, 'body': 'b5'}, {'id': 'c6', 'author': 'u6', 'created_utc': 600, 'body': 'b6'}]},
        {'id': 't3', 'children': [{'id': 'c7', 'author': 'u7', 'created_utc': 700, 'body': 'b7'}]} # Only 1 child, should be excluded
    ]
    
    with open(input_file, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    
    # Create exclusion log for t2
    with open(exclusion_file, 'w') as f:
        f.write('t2\n')
    
    # Run extraction
    run_extraction(input_file, exclusion_file, output_file, seed_count_threshold=3)
    
    # Verify output
    assert output_file.exists()
    df = pd.read_csv(output_file)
    assert len(df) == 1 # Only t1 should remain
    assert df.iloc[0]['thread_id'] == 't1'
    
    # Verify exclusion log was created
    exclusions_log = tmp_path / "exclusions_run.log"
    assert exclusions_log.exists()
    with open(exclusions_log, 'r') as f:
        lines = f.readlines()
    # t2 excluded (log), t3 excluded (seed insufficient)
    assert len(lines) == 2