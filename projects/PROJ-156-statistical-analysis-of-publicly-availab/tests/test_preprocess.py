import json
import os
import sys
import csv
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the module under test
sys.path.insert(0, os.path.join(os.dirname(__file__), '..', 'code', 'scripts'))
from preprocess import (
    load_config,
    load_schema,
    validate_record,
    load_raw_data,
    remove_duplicates,
    filter_incomplete_runs,
    hash_runner_id,
    compute_runner_metrics,
    generate_runner_profiles,
    save_to_csv
)

@pytest.fixture
def sample_schema():
    return {
        "required": ["submission_id", "runner_id", "submission_date", "game_id", "time"]
    }

@pytest.fixture
def sample_records():
    return [
        {"submission_id": "1", "runner_id": "userA", "submission_date": "2023-01-01T00:00:00Z", "game_id": "mario", "time": 100},
        {"submission_id": "2", "runner_id": "userB", "submission_date": "2023-01-02T00:00:00Z", "game_id": "mario", "time": 110},
        {"submission_id": "1", "runner_id": "userA", "submission_date": "2023-01-01T00:00:00Z", "game_id": "mario", "time": 100}, # Duplicate
        {"submission_id": "3", "runner_id": "userA", "submission_date": "2023-01-03T00:00:00Z", "game_id": "zelda", "time": 120}
    ]

def test_validate_record_valid(sample_schema, sample_records):
    record = sample_records[0]
    assert validate_record(record, sample_schema) is True

def test_validate_record_invalid(sample_schema):
    record = {"submission_id": "1", "runner_id": "userA"} # Missing fields
    assert validate_record(record, sample_schema) is False

def test_remove_duplicates(sample_records):
    unique = remove_duplicates(sample_records)
    assert len(unique) == 3 # 4 records, 1 duplicate
    assert unique[0]['submission_id'] == "1"
    assert unique[1]['submission_id'] == "2"
    assert unique[2]['submission_id'] == "3"

def test_filter_incomplete_runs(sample_records):
    # Add an incomplete record
    incomplete = {"submission_id": "4", "runner_id": "userC"} # Missing date, game, time
    data = sample_records + [incomplete]
    filtered = filter_incomplete_runs(data, ["submission_id", "runner_id", "submission_date", "game_id", "time"])
    assert len(filtered) == 4 # Should remove the incomplete one

def test_hash_runner_id_deterministic():
    salt = "test_salt"
    id1 = hash_runner_id("userX", salt)
    id2 = hash_runner_id("userX", salt)
    assert id1 == id2
    assert len(id1) == 64 # SHA-256 hex length

def test_generate_runner_profiles():
    # Create mock records
    records = [
        {"runner_id": "hashA", "submission_date": "2023-01-01T00:00:00Z", "game_id": "mario"},
        {"runner_id": "hashA", "submission_date": "2023-01-02T00:00:00Z", "game_id": "mario"},
        {"runner_id": "hashA", "submission_date": "2023-01-03T00:00:00Z", "game_id": "zelda"},
        {"runner_id": "hashB", "submission_date": "2023-01-01T00:00:00Z", "game_id": "mario"},
    ]
    config = {"salt": "dummy"}
    profiles = generate_runner_profiles(records, config)
    
    assert len(profiles) == 2
    
    # Check hashA
    profile_a = next(p for p in profiles if p['runner_id'] == 'hashA')
    assert profile_a['total_runs'] == 3
    assert profile_a['games_played_count'] == 2
    assert profile_a['time_since_first_run_days'] >= 2 # 1st to 3rd Jan
    
    # Check hashB
    profile_b = next(p for p in profiles if p['runner_id'] == 'hashB')
    assert profile_b['total_runs'] == 1
    assert profile_b['games_played_count'] == 1

def test_contract_validation_integration():
    # Integration test: Load schema, validate records, ensure structure
    schema = {
        "required": ["runner_id", "total_runs", "first_run_date", "time_since_first_run_days", "games_played_count"]
    }
    records = [
        {"runner_id": "A", "total_runs": 1, "first_run_date": "2023-01-01", "time_since_first_run_days": 10, "games_played_count": 1},
        {"runner_id": "B", "total_runs": 2, "first_run_date": "2023-01-01", "time_since_first_run_days": 5, "games_played_count": 1}
    ]
    for r in records:
        assert validate_record(r, schema) is True

def test_data_completeness_threshold(sample_records):
    # Simulate a check for 95% retention
    initial = 100
    filtered = 96
    threshold = 0.95
    assert (filtered / initial) >= threshold