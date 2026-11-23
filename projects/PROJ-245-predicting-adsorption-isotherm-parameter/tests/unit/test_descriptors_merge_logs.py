"""
Unit tests for descriptor log merging functionality.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

from code.data.descriptors import merge_descriptor_logs

def test_merge_descriptor_logs_empty():
    """Test merging logs when no log files exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "missing_descriptors_report.json")
        
        result = merge_descriptor_logs(base_path=tmpdir, output_path=output_path)
        
        assert result["total_failures"] == 0
        assert result["kinetic_diameter_failures"] == []
        assert result["lj_epsilon_failures"] == []
        assert result["quadrupole_moment_failures"] == []
        assert result["summary"]["total_failures"] == 0
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Verify file contents
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
            assert saved_result == result

def test_merge_descriptor_logs_with_data():
    """Test merging logs with actual failure data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock log files
        kinetic_log = os.path.join(tmpdir, "missing_descriptors_kinetic.json")
        lj_log = os.path.join(tmpdir, "missing_descriptors_lj.json")
        quadrupole_log = os.path.join(tmpdir, "missing_descriptors_quadrupole.json")
        
        kinetic_data = [
            {"index": 1, "reason": "invalid_smiles", "smiles": "C1"},
            {"index": 2, "reason": "calculation_error"}
        ]
        lj_data = [
            {"index": 3, "reason": "missing_data"}
        ]
        quadrupole_data = []
        
        with open(kinetic_log, 'w') as f:
            json.dump(kinetic_data, f)
        with open(lj_log, 'w') as f:
            json.dump(lj_data, f)
        with open(quadrupole_log, 'w') as f:
            json.dump(quadrupole_data, f)
        
        output_path = os.path.join(tmpdir, "missing_descriptors_report.json")
        
        result = merge_descriptor_logs(base_path=tmpdir, output_path=output_path)
        
        assert result["total_failures"] == 3
        assert len(result["kinetic_diameter_failures"]) == 2
        assert len(result["lj_epsilon_failures"]) == 1
        assert len(result["quadrupole_moment_failures"]) == 0
        assert result["summary"]["total_failures"] == 3
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Verify file contents match result
        with open(output_path, 'r') as f:
            saved_result = json.load(f)
            assert saved_result == result

def test_merge_descriptor_logs_invalid_json():
    """Test merging logs when log files contain invalid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create invalid JSON files
        kinetic_log = os.path.join(tmpdir, "missing_descriptors_kinetic.json")
        lj_log = os.path.join(tmpdir, "missing_descriptors_lj.json")
        quadrupole_log = os.path.join(tmpdir, "missing_descriptors_quadrupole.json")
        
        with open(kinetic_log, 'w') as f:
            f.write("invalid json {")
        with open(lj_log, 'w') as f:
            f.write("invalid json {")
        with open(quadrupole_log, 'w') as f:
            f.write("invalid json {")
        
        output_path = os.path.join(tmpdir, "missing_descriptors_report.json")
        
        # Should not raise an exception
        result = merge_descriptor_logs(base_path=tmpdir, output_path=output_path)
        
        assert result["total_failures"] == 0
        assert result["kinetic_diameter_failures"] == []
        assert result["lj_epsilon_failures"] == []
        assert result["quadrupole_moment_failures"] == []