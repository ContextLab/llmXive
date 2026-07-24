import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import yaml

from code.analysis.verify_schemas import (
    load_schema,
    validate_csv_schema,
    validate_json_schema,
    run_schema_validation,
    compute_file_hash
)

@pytest.fixture
def temp_contracts_dir():
    """Create a temporary contracts directory with test schemas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        contracts_dir = Path(tmpdir) / "contracts"
        contracts_dir.mkdir()
        
        # Create a test thread schema
        thread_schema = {
            "name": "thread",
            "columns": {
                "thread_id": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "created_utc": {"type": "timestamp", "required": True},
                "subreddit": {"type": "string", "required": True},
                "author": {"type": "string", "required": True},
                "upvote_ratio": {"type": "float", "required": False}
            }
        }
        
        with open(contracts_dir / "thread.schema.yaml", 'w') as f:
            yaml.dump(thread_schema, f)
            
        yield contracts_dir

@pytest.fixture
def temp_processed_dir():
    """Create a temporary processed directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_dir = Path(tmpdir) / "processed"
        processed_dir.mkdir()
        
        # Create a valid CSV file
        valid_df = pd.DataFrame({
            'thread_id': ['t1', 't2', 't3'],
            'title': ['Title 1', 'Title 2', 'Title 3'],
            'created_utc': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'subreddit': ['r/test', 'r/test2', 'r/test3'],
            'author': ['user1', 'user2', 'user3'],
            'upvote_ratio': [0.8, 0.9, 0.7]
        })
        valid_df.to_csv(processed_dir / "thread.csv", index=False)
        
        # Create an invalid CSV file (missing required column)
        invalid_df = pd.DataFrame({
            'thread_id': ['t1', 't2'],
            'title': ['Title 1', 'Title 2'],
            'created_utc': ['2023-01-01', '2023-01-02']
            # Missing subreddit, author
        })
        invalid_df.to_csv(processed_dir / "thread_invalid.csv", index=False)
        
        # Create a valid JSON file
        valid_json = {
            "thread_id": "t1",
            "title": "Test Thread",
            "created_utc": "2023-01-01",
            "subreddit": "r/test",
            "author": "user1",
            "upvote_ratio": 0.8
        }
        
        with open(processed_dir / "valid_thread.json", 'w') as f:
            json.dump(valid_json, f)
        
        yield processed_dir

def test_load_schema(temp_contracts_dir):
    """Test loading a schema file."""
    schema = load_schema("thread.schema.yaml")
    assert schema is not None
    assert "columns" in schema
    assert "thread_id" in schema["columns"]
    assert schema["columns"]["thread_id"]["required"] is True

def test_validate_csv_schema_valid(temp_contracts_dir, temp_processed_dir):
    """Test validating a valid CSV file."""
    # Temporarily override the CONTRACTS_DIR and PROCESSED_DIR
    import code.analysis.verify_schemas as vs
    original_contracts = vs.CONTRACTS_DIR
    original_processed = vs.PROCESSED_DIR
    
    vs.CONTRACTS_DIR = temp_contracts_dir
    vs.PROCESSED_DIR = temp_processed_dir / "processed"
    
    try:
        schema = load_schema("thread.schema.yaml")
        errors = validate_csv_schema(temp_processed_dir / "thread.csv", schema)
        assert len(errors) == 0
    finally:
        vs.CONTRACTS_DIR = original_contracts
        vs.PROCESSED_DIR = original_processed

def test_validate_csv_schema_invalid(temp_contracts_dir, temp_processed_dir):
    """Test validating an invalid CSV file."""
    import code.analysis.verify_schemas as vs
    original_contracts = vs.CONTRACTS_DIR
    original_processed = vs.PROCESSED_DIR
    
    vs.CONTRACTS_DIR = temp_contracts_dir
    vs.PROCESSED_DIR = temp_processed_dir / "processed"
    
    try:
        schema = load_schema("thread.schema.yaml")
        errors = validate_csv_schema(temp_processed_dir / "thread_invalid.csv", schema)
        assert len(errors) > 0
        assert any("Missing required columns" in error for error in errors)
    finally:
        vs.CONTRACTS_DIR = original_contracts
        vs.PROCESSED_DIR = original_processed

def test_validate_json_schema_valid(temp_contracts_dir, temp_processed_dir):
    """Test validating a valid JSON file."""
    import code.analysis.verify_schemas as vs
    original_contracts = vs.CONTRACTS_DIR
    original_processed = vs.PROCESSED_DIR
    
    vs.CONTRACTS_DIR = temp_contracts_dir
    vs.PROCESSED_DIR = temp_processed_dir / "processed"
    
    try:
        schema = load_schema("thread.schema.yaml")
        # For JSON validation, we need a schema with properties
        json_schema = {
            "properties": {
                "thread_id": {"type": "string", "required": True},
                "title": {"type": "string", "required": True},
                "created_utc": {"type": "string", "required": True},
                "subreddit": {"type": "string", "required": True},
                "author": {"type": "string", "required": True},
                "upvote_ratio": {"type": "float", "required": False}
            }
        }
        errors = validate_json_schema(temp_processed_dir / "valid_thread.json", json_schema)
        assert len(errors) == 0
    finally:
        vs.CONTRACTS_DIR = original_contracts
        vs.PROCESSED_DIR = original_processed

def test_compute_file_hash(temp_processed_dir):
    """Test file hash computation."""
    file_path = temp_processed_dir / "thread.csv"
    hash1 = compute_file_hash(file_path)
    hash2 = compute_file_hash(file_path)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex string length

def test_run_schema_validation(temp_contracts_dir, temp_processed_dir, monkeypatch):
    """Test running the full schema validation."""
    import code.analysis.verify_schemas as vs
    original_contracts = vs.CONTRACTS_DIR
    original_processed = vs.PROCESSED_DIR
    original_state = vs.STATE_DIR
    original_report_path = vs.REPORT_PATH
    
    with tempfile.TemporaryDirectory() as tmpdir:
        vs.CONTRACTS_DIR = temp_contracts_dir
        vs.PROCESSED_DIR = temp_processed_dir
        vs.STATE_DIR = Path(tmpdir)
        vs.REPORT_PATH = vs.STATE_DIR / "schema_validation_report.json"
        
        try:
            report = run_schema_validation()
            
            assert "status" in report
            assert "files_checked" in report
            assert "errors" in report
            assert report["files_checked"] > 0
            
            # The report should pass if we have valid files
            # Note: This depends on the actual schema matching logic
        finally:
            vs.CONTRACTS_DIR = original_contracts
            vs.PROCESSED_DIR = original_processed
            vs.STATE_DIR = original_state
            vs.REPORT_PATH = original_report_path