"""
Unit tests for memory profiling functionality.

Tests verify that the memory profiling script runs correctly and
generates valid output.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.profile_memory import get_current_memory_mb, generate_memory_report

class TestMemoryProfile:
    """Test cases for memory profiling utilities."""

    def test_get_current_memory_mb_returns_positive_float(self):
        """Test that memory measurement returns a positive float."""
        memory = get_current_memory_mb()
        assert isinstance(memory, float)
        assert memory > 0, "Memory usage should be positive"

    def test_generate_memory_report_creates_file(self):
        """Test that the report generator creates the output file."""
        profile_stats = {
            'initial_memory_mb': 100.0,
            'peak_memory_mb': 200.0,
            'final_memory_mb': 150.0,
            'total_memory_delta_mb': 50.0,
            'stages': [
                {
                    'name': 'test_stage',
                    'duration_seconds': 1.0,
                    'memory_start_mb': 100.0,
                    'memory_end_mb': 150.0,
                    'memory_delta_mb': 50.0
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            generate_memory_report(profile_stats, output_path)
            
            assert output_path.exists(), "Report file should be created"
            content = output_path.read_text()
            assert "# Memory Profile Report" in content, "Report should have title"
            assert "200.00 MB" in content, "Report should contain peak memory"
            assert "PASS" in content, "Report should indicate compliance status"

    def test_generate_memory_report_contains_required_sections(self):
        """Test that the report contains all required sections."""
        profile_stats = {
            'initial_memory_mb': 100.0,
            'peak_memory_mb': 200.0,
            'final_memory_mb': 150.0,
            'total_memory_delta_mb': 50.0,
            'stages': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            generate_memory_report(profile_stats, output_path)
            
            content = output_path.read_text()
            
            required_sections = [
                "## Overview",
                "## Configuration",
                "## Results Summary",
                "## Compliance Check",
                "## Stage-by-Stage Breakdown",
                "## Analysis",
                "## Recommendations",
                "## Methodology"
            ]
            
            for section in required_sections:
                assert section in content, f"Report should contain section: {section}"

    def test_compliance_check_passes_under_limit(self):
        """Test that compliance check passes when under 7GB limit."""
        profile_stats = {
            'initial_memory_mb': 100.0,
            'peak_memory_mb': 5000.0,  # Under 7168 MB
            'final_memory_mb': 150.0,
            'total_memory_delta_mb': 50.0,
            'stages': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            generate_memory_report(profile_stats, output_path)
            
            content = output_path.read_text()
            assert "PASS" in content, "Should pass when under limit"
            assert "7168 MB" in content, "Should reference the limit"

    def test_compliance_check_fails_over_limit(self):
        """Test that compliance check fails when over 7GB limit."""
        profile_stats = {
            'initial_memory_mb': 100.0,
            'peak_memory_mb': 8000.0,  # Over 7168 MB
            'final_memory_mb': 150.0,
            'total_memory_delta_mb': 50.0,
            'stages': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.md"
            generate_memory_report(profile_stats, output_path)
            
            content = output_path.read_text()
            assert "FAIL" in content, "Should fail when over limit"