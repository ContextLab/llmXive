"""
Unit tests for code/engines/save_processed_logs.py (Task T025)
"""
import json
import os
import tempfile
import pytest
from pathlib import Path

from code.engines.save_processed_logs import (
    load_json_file,
    save_json_file,
    process_execution_log,
    save_processed_logs,
    main
)

def test_process_execution_log_valid():
    """Test processing a valid execution log."""
    log_data = {
        "workflow_id": "wf-001",
        "compression_depth": 2,
        "token_count": 1500,
        "policy_violations": [
            {"node_id": "n1", "rule_id": "r1"}
        ],
        "context_reduction_pct": 15.5,
        "status": "normal",
        "is_valid": True
    }
    
    processed = process_execution_log(log_data)
    
    assert processed["workflow_id"] == "wf-001"
    assert processed["compression_depth"] == 2
    assert processed["context_reduction_pct"] == 15.5
    assert processed["status"] == "normal"
    assert processed["is_valid"] is True
    assert len(processed["violation_details"]) == 1
    assert processed["violation_details"][0]["node_id"] == "n1"

def test_process_execution_log_edge_case_deferred():
    """Test processing an edge case log with [deferred] status."""
    log_data = {
        "workflow_id": "wf-edge",
        "compression_depth": 0,
        "token_count": 0,
        "policy_violations": [],
        "context_reduction_pct": "[deferred]",
        "status": "edge_case",
        "is_valid": True
    }
    
    processed = process_execution_log(log_data)
    
    assert processed["context_reduction_pct"] == "[deferred]"
    assert processed["status"] == "edge_case"

def test_process_execution_log_missing_violations():
    """Test that missing policy_violations defaults to empty list."""
    log_data = {
        "workflow_id": "wf-002",
        "compression_depth": 1,
        "token_count": 100
    }
    
    processed = process_execution_log(log_data)
    assert processed["policy_violations"] == []
    assert processed["violation_details"] == []

def test_save_processed_logs_integration():
    """Test saving logs to disk."""
    logs = [
        {
            "workflow_id": "wf-001",
            "compression_depth": 1,
            "token_count": 500,
            "policy_violations": [],
            "context_reduction_pct": 10.0,
            "status": "normal",
            "is_valid": True
        },
        {
            "workflow_id": "wf-002",
            "compression_depth": 2,
            "token_count": 450,
            "policy_violations": [{"node_id": "n2", "rule_id": "r2"}],
            "context_reduction_pct": 20.0,
            "status": "normal",
            "is_valid": True
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        saved_files = save_processed_logs(logs, tmpdir)
        
        assert len(saved_files) == 2
        
        # Check file names
        assert any("log_wf-001_1.json" in f for f in saved_files)
        assert any("log_wf-002_2.json" in f for f in saved_files)
        
        # Verify content
        for f_path in saved_files:
            with open(f_path, 'r') as f:
                data = json.load(f)
                assert "workflow_id" in data
                assert "compression_depth" in data
                assert "token_count" in data
                assert "policy_violations" in data