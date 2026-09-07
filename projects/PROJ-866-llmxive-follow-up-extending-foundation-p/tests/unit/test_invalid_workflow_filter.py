"""
Unit tests for the invalid workflow filter module.

These tests verify that the filter correctly identifies and excludes
invalid workflows based on their execution logs.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from engines.invalid_workflow_filter import (
    load_execution_log,
    is_workflow_valid,
    filter_invalid_workflows
)


class TestLoadExecutionLog:
    """Tests for the load_execution_log function."""
    
    def test_load_valid_log(self):
        """Test loading a valid execution log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_log.json"
            test_data = {
                "workflow_id": "test-123",
                "is_valid": True,
                "status": "normal"
            }
            with open(log_path, 'w') as f:
                json.dump(test_data, f)
            
            result = load_execution_log(log_path)
            assert result is not None
            assert result["workflow_id"] == "test-123"
            assert result["is_valid"] is True
    
    def test_load_invalid_json(self):
        """Test loading an invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "invalid.json"
            with open(log_path, 'w') as f:
                f.write("not valid json")
            
            result = load_execution_log(log_path)
            assert result is None
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        log_path = Path("/nonexistent/path/file.json")
        result = load_execution_log(log_path)
        assert result is None


class TestIsWorkflowValid:
    """Tests for the is_workflow_valid function."""
    
    def test_valid_workflow(self):
        """Test that a workflow with is_valid=True is considered valid."""
        log = {"is_valid": True, "workflow_id": "test-1"}
        assert is_workflow_valid(log) is True
    
    def test_invalid_workflow(self):
        """Test that a workflow with is_valid=False is considered invalid."""
        log = {"is_valid": False, "workflow_id": "test-2"}
        assert is_workflow_valid(log) is False
    
    def test_missing_is_valid_field(self):
        """Test that a workflow without is_valid field is considered valid."""
        log = {"workflow_id": "test-3", "status": "normal"}
        assert is_workflow_valid(log) is True
    
    def test_is_valid_none(self):
        """Test that a workflow with is_valid=None is considered valid."""
        log = {"is_valid": None, "workflow_id": "test-4"}
        assert is_workflow_valid(log) is True


class TestFilterInvalidWorkflows:
    """Tests for the filter_invalid_workflows function."""
    
    def test_filter_mixed_workflows(self):
        """Test filtering with a mix of valid and invalid workflows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            logs_dir.mkdir()
            
            # Create valid workflow logs
            valid_logs = [
                {"workflow_id": "valid-1", "is_valid": True},
                {"workflow_id": "valid-2", "is_valid": True},
                {"workflow_id": "valid-3"},  # No is_valid field
            ]
            
            # Create invalid workflow logs
            invalid_logs = [
                {"workflow_id": "invalid-1", "is_valid": False},
                {"workflow_id": "invalid-2", "is_valid": False},
            ]
            
            # Write logs to files
            for i, log in enumerate(valid_logs):
                with open(logs_dir / f"valid_{i}.json", 'w') as f:
                    json.dump(log, f)
            
            for i, log in enumerate(invalid_logs):
                with open(logs_dir / f"invalid_{i}.json", 'w') as f:
                    json.dump(log, f)
            
            # Run filter
            valid_workflows, invalid_workflows = filter_invalid_workflows(logs_dir)
            
            # Verify results
            assert len(valid_workflows) == 3
            assert len(invalid_workflows) == 2
            assert set(valid_workflows) == {"valid-1", "valid-2", "valid-3"}
            assert set(invalid_workflows) == {"invalid-1", "invalid-2"}
    
    def test_filter_empty_directory(self):
        """Test filtering an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            logs_dir.mkdir()
            
            valid_workflows, invalid_workflows = filter_invalid_workflows(logs_dir)
            
            assert len(valid_workflows) == 0
            assert len(invalid_workflows) == 0
    
    def test_filter_with_output(self):
        """Test filtering with output directory specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_dir = Path(tmpdir) / "logs"
            logs_dir.mkdir()
            output_dir = Path(tmpdir) / "output"
            
            # Create a valid and an invalid log
            with open(logs_dir / "valid.json", 'w') as f:
                json.dump({"workflow_id": "valid-1", "is_valid": True}, f)
            with open(logs_dir / "invalid.json", 'w') as f:
                json.dump({"workflow_id": "invalid-1", "is_valid": False}, f)
            
            valid_workflows, invalid_workflows = filter_invalid_workflows(
                logs_dir, output_dir
            )
            
            # Verify summary file was created
            summary_path = output_dir / "invalid_workflow_filter_summary.json"
            assert summary_path.exists()
            
            with open(summary_path, 'r') as f:
                summary = json.load(f)
            
            assert summary["total_workflows"] == 2
            assert summary["valid_workflows"] == 1
            assert summary["invalid_workflows"] == 1
            assert "valid-1" in summary["valid_workflow_ids"]
            assert "invalid-1" in summary["invalid_workflow_ids"]
    
    def test_filter_nonexistent_directory(self):
        """Test filtering a non-existent directory."""
        logs_dir = Path("/nonexistent/directory")
        valid_workflows, invalid_workflows = filter_invalid_workflows(logs_dir)
        
        assert len(valid_workflows) == 0
        assert len(invalid_workflows) == 0