"""
Unit tests for T067: Verify Invalid Workflow Exclusion
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.verify_invalid_workflow_exclusion import load_raw_workflows, verify_exclusion

def test_load_raw_workflows_valid_and_invalid():
    """Test loading workflows with mixed validity flags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir)
        
        # Create a synthetic workflow file
        workflows = [
            {"id": "wf_valid_1", "is_valid": True},
            {"id": "wf_valid_2", "is_valid": True},
            {"id": "wf_invalid_1", "is_valid": False},
            {"id": "wf_invalid_2", "is_valid": False},
        ]
        
        file_path = raw_dir / "workflows_test.json"
        with open(file_path, 'w') as f:
            json.dump(workflows, f)
        
        result = load_raw_workflows(raw_dir)
        
        assert len(result) == 4
        assert result["wf_valid_1"] is True
        assert result["wf_valid_2"] is True
        assert result["wf_invalid_1"] is False
        assert result["wf_invalid_2"] is False

def test_verify_exclusion_success():
    """Test that verification passes when invalid workflows are excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        results_dir = Path(tmpdir) / "results"
        
        raw_dir.mkdir()
        processed_dir.mkdir()
        results_dir.mkdir()
        
        # Create raw workflows
        raw_workflows = [
            {"id": "wf_valid", "is_valid": True},
            {"id": "wf_invalid", "is_valid": False},
        ]
        with open(raw_dir / "workflows.json", 'w') as f:
            json.dump(raw_workflows, f)
        
        # Create processed logs (only valid workflow)
        valid_log = {"workflow_id": "wf_valid", "is_valid": True}
        with open(processed_dir / "log_wf_valid.json", 'w') as f:
            json.dump(valid_log, f)
        
        # Create dummy results files
        with open(results_dir / "tradeoff_curve.csv", 'w') as f:
            f.write("reduction_pct,error_rate\n10,0.01\n")
        with open(results_dir / "threshold_ci.json", 'w') as f:
            json.dump({"threshold": 15.5}, f)
        
        # Run verification
        success = verify_exclusion(raw_dir, results_dir)
        
        assert success is True

def test_verify_exclusion_failure():
    """Test that verification fails when an invalid workflow is present in processed logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        raw_dir = Path(tmpdir) / "raw"
        processed_dir = Path(tmpdir) / "processed"
        results_dir = Path(tmpdir) / "results"
        
        raw_dir.mkdir()
        processed_dir.mkdir()
        results_dir.mkdir()
        
        # Create raw workflows
        raw_workflows = [
            {"id": "wf_valid", "is_valid": True},
            {"id": "wf_invalid", "is_valid": False},
        ]
        with open(raw_dir / "workflows.json", 'w') as f:
            json.dump(raw_workflows, f)
        
        # Create processed logs (includes invalid workflow)
        valid_log = {"workflow_id": "wf_valid", "is_valid": True}
        invalid_log = {"workflow_id": "wf_invalid", "is_valid": False}
        
        with open(processed_dir / "log_wf_valid.json", 'w') as f:
            json.dump(valid_log, f)
        with open(processed_dir / "log_wf_invalid.json", 'w') as f:
            json.dump(invalid_log, f)
        
        # Create dummy results files
        with open(results_dir / "tradeoff_curve.csv", 'w') as f:
            f.write("reduction_pct,error_rate\n10,0.01\n")
        with open(results_dir / "threshold_ci.json", 'w') as f:
            json.dump({"threshold": 15.5}, f)
        
        # Run verification
        success = verify_exclusion(raw_dir, results_dir)
        
        assert success is False