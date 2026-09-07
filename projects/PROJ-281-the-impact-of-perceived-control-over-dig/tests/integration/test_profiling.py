"""
Integration tests for the performance profiling module.

These tests verify that the profiling system correctly:
1. Measures runtime and memory usage
2. Validates against defined limits
3. Detects Plan/Spec discrepancies
4. Generates valid reports
"""
import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.profiling import (
    get_memory_usage_gb,
    get_peak_memory_gb,
    check_plan_spec_discrepancy,
    run_profiling_pipeline,
    save_report,
    RuntimeLimitExceededError,
    MemoryLimitExceededError,
    RUNTIME_LIMIT_HOURS,
    RAM_LIMIT_GB
)

class TestMemoryFunctions:
    """Tests for memory measurement functions."""
    
    def test_get_memory_usage_gb_returns_positive(self):
        """Test that get_memory_usage_gb returns a positive number."""
        memory = get_memory_usage_gb()
        assert memory >= 0, "Memory usage should be non-negative"
        
    def test_get_peak_memory_gb_returns_positive(self):
        """Test that get_peak_memory_gb returns a positive number."""
        peak_memory = get_peak_memory_gb()
        assert peak_memory >= 0, "Peak memory should be non-negative"
        
    def test_peak_memory_gte_current_memory(self):
        """Test that peak memory is at least current memory."""
        current = get_memory_usage_gb()
        peak = get_peak_memory_gb()
        assert peak >= current, "Peak memory should be >= current memory"

class TestDiscrepancyCheck:
    """Tests for Plan/Spec discrepancy checking."""
    
    def test_no_discrepancy_when_both_say_6h(self, tmp_path):
        """Test that no discrepancy is found when both files agree on 6h limit."""
        plan_path = tmp_path / "plan.md"
        spec_path = tmp_path / "specs" / "001-the-impact-of-perceived-control-over-dig" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        
        plan_path.write_text("""
        # Plan
        
        ## Compute Feasibility Note
        The pipeline is designed to run within 6 hours.
        """)
        
        spec_path.write_text("""
        # Specification
        
        ## SC-004
        Hard 6h runtime limit.
        """)
        
        # Temporarily change global paths
        from code import profiling
        original_plan_path = profiling.PLAN_PATH
        original_spec_path = profiling.SPEC_PATH
        
        profiling.PLAN_PATH = plan_path
        profiling.SPEC_PATH = spec_path
        
        try:
            discrepancy = check_plan_spec_discrepancy()
            assert discrepancy is None, "No discrepancy should be found when both agree"
        finally:
            profiling.PLAN_PATH = original_plan_path
            profiling.SPEC_PATH = original_spec_path
            
    def test_discrepancy_when_plan_says_different_limit(self, tmp_path):
        """Test that discrepancy is found when Plan mentions different limit."""
        plan_path = tmp_path / "plan.md"
        spec_path = tmp_path / "specs" / "001-the-impact-of-perceived-control-over-dig" / "spec.md"
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        
        plan_path.write_text("""
        # Plan
        
        ## Compute Feasibility Note
        The pipeline is designed to run within 4 hours for optimization.
        """)
        
        spec_path.write_text("""
        # Specification
        
        ## SC-004
        Hard 6h runtime limit.
        """)
        
        from code import profiling
        original_plan_path = profiling.PLAN_PATH
        original_spec_path = profiling.SPEC_PATH
        
        profiling.PLAN_PATH = plan_path
        profiling.SPEC_PATH = spec_path
        
        try:
            discrepancy = check_plan_spec_discrepancy()
            assert discrepancy is not None, "Discrepancy should be found when limits differ"
            assert "contradicts" in discrepancy.lower()
        finally:
            profiling.PLAN_PATH = original_plan_path
            profiling.SPEC_PATH = original_spec_path

class TestReportSaving:
    """Tests for report saving functionality."""
    
    def test_save_report_creates_file(self, tmp_path):
        """Test that save_report creates the output file."""
        results = {
            "runtime_seconds": 100,
            "peak_memory_gb": 2.5,
            "validation": {"overall_ok": True}
        }
        
        output_path = tmp_path / "test_report.json"
        
        save_report(results, output_path=str(output_path))
        
        assert output_path.exists(), "Report file should be created"
        
        with open(output_path) as f:
            saved_results = json.load(f)
            
        assert saved_results == results
        
    def test_save_report_creates_directories(self, tmp_path):
        """Test that save_report creates parent directories if needed."""
        results = {"test": "data"}
        
        nested_path = tmp_path / "deep" / "nested" / "path" / "report.json"
        
        save_report(results, output_path=str(nested_path))
        
        assert nested_path.exists(), "Nested directories should be created"

class TestProfilingPipeline:
    """Tests for the full profiling pipeline."""
    
    def test_pipeline_validates_runtime_limit(self):
        """Test that pipeline correctly validates runtime against limit."""
        # Mock time to simulate long runtime
        with patch('code.profiling.time.time') as mock_time:
            mock_time.side_effect = [0, 6 * 3600 + 100]  # Start at 0, end after 6h
            
            results = run_profiling_pipeline()
            
            assert not results["validation"]["runtime_ok"]
            assert results["runtime_seconds"] > 6 * 3600
            
    def test_pipeline_validates_memory_limit(self):
        """Test that pipeline correctly validates memory against limit."""
        # Mock memory functions to simulate high memory usage
        with patch('code.profiling.get_peak_memory_gb', return_value=10.0):
            with patch('code.profiling.run_pipeline', return_value=None):
                results = run_profiling_pipeline()
                
                assert not results["validation"]["memory_ok"]
                assert results["peak_memory_gb"] == 10.0
                
    def test_pipeline_passes_when_within_limits(self):
        """Test that pipeline passes when within all limits."""
        with patch('code.profiling.time.time') as mock_time:
            mock_time.side_effect = [0, 100]  # 100 seconds runtime
            
            with patch('code.profiling.get_peak_memory_gb', return_value=2.0):
                with patch('code.profiling.run_pipeline', return_value=None):
                    results = run_profiling_pipeline()
                    
                    assert results["validation"]["overall_ok"]
                    assert results["validation"]["runtime_ok"]
                    assert results["validation"]["memory_ok"]

class TestIntegrationWithPipeline:
    """Integration tests with the actual pipeline."""
    
    @pytest.mark.skip(reason="Requires actual pipeline execution")
    def test_full_pipeline_profiling(self):
        """Test profiling the full pipeline execution."""
        # This test would run the actual pipeline and verify profiling
        # It's skipped because it requires significant resources
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
