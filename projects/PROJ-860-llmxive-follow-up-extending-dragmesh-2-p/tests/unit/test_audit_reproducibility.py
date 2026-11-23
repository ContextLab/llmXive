"""
Unit tests for the reproducibility audit script (T039).
"""
import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from audit_reproducibility import (
    get_dependency_hashes,
    get_environment_info,
    get_seed_configuration,
    generate_audit_report
)
from seed_config import set_seeds, init_reproducibility

class TestAuditReproducibility:
    """Tests for the reproducibility audit functionality."""

    def test_dependency_hashes_exist(self):
        """Test that dependency hashes are generated correctly."""
        hashes = get_dependency_hashes()
        assert isinstance(hashes, dict)
        # At minimum, we should have the requirements.txt hash if it exists
        if os.path.exists("code/requirements.txt"):
            assert "requirements.txt" in hashes

    def test_environment_info_structure(self):
        """Test that environment info contains required fields."""
        info = get_environment_info()
        
        assert "timestamp" in info
        assert "platform" in info
        assert "python" in info
        assert "environment_variables" in info
        
        # Check platform fields
        platform_info = info["platform"]
        assert "system" in platform_info
        assert "machine" in platform_info
        
        # Check python fields
        python_info = info["python"]
        assert "version" in python_info

    def test_seed_configuration(self):
        """Test that seed configuration is properly retrieved."""
        # First, initialize reproducibility
        init_reproducibility()
        
        seeds = get_seed_configuration()
        assert "status" in seeds
        assert seeds["status"] == "configured"
        assert "global_seed" in seeds

    def test_generate_audit_report(self):
        """Test that an audit report is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_audit.json")
            
            report = generate_audit_report(output_path)
            
            # Verify file was created
            assert os.path.exists(output_path)
            
            # Verify report structure
            assert "audit_metadata" in report
            assert "environment" in report
            assert "seeds" in report
            assert "dependencies" in report
            
            # Verify metadata fields
            metadata = report["audit_metadata"]
            assert "task_id" in metadata
            assert metadata["task_id"] == "T039"
            assert "generated_at" in metadata

    def test_report_is_valid_json(self):
        """Test that the generated report is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_audit.json")
            
            generate_audit_report(output_path)
            
            with open(output_path, 'r') as f:
                loaded_report = json.load(f)
            
            assert isinstance(loaded_report, dict)
            assert len(loaded_report) > 0

    def test_cpu_only_enforcement_in_report(self):
        """Test that the report correctly identifies CUDA availability."""
        info = get_environment_info()
        
        # The field should exist
        assert "torch_cuda_available" in info["environment_variables"] or "torch_cuda_available" in info
        
        # If torch is available, it should be explicitly marked
        if "torch_cuda_available" in info:
            assert isinstance(info["torch_cuda_available"], bool)

    def test_reproducibility_seeds_captured(self):
        """Test that all relevant seeds are captured in the audit."""
        init_reproducibility()
        seeds = get_seed_configuration()
        
        assert "global_seed" in seeds
        assert isinstance(seeds["global_seed"], int)