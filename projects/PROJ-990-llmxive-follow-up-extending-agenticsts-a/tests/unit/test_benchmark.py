"""
Unit tests for the benchmark module.
"""
import pytest
import time
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from benchmark import (
    get_memory_usage_mb,
    run_phase_benchmark,
    run_full_benchmark,
    save_benchmark_report,
    main
)

class TestMemoryUsage:
    """Tests for memory usage calculation."""
    
    def test_get_memory_usage_mb_returns_number(self):
        """Test that memory usage function returns a numeric value."""
        memory = get_memory_usage_mb()
        assert isinstance(memory, (int, float))
        assert memory >= 0

class TestPhaseBenchmark:
    """Tests for phase benchmarking functionality."""
    
    def test_run_phase_benchmark_success(self):
        """Test successful phase execution."""
        def dummy_func():
            time.sleep(0.01)
            return "result"
        
        result = run_phase_benchmark("test_phase", dummy_func)
        
        assert result["phase_name"] == "test_phase"
        assert result["duration_seconds"] >= 0.01
        assert result["success"] is True
        assert result["error"] is None
        assert "timestamp" in result
    
    def test_run_phase_benchmark_failure(self):
        """Test phase execution with exception."""
        def failing_func():
            raise ValueError("Test error")
        
        result = run_phase_benchmark("failing_phase", failing_func)
        
        assert result["phase_name"] == "failing_phase"
        assert result["success"] is False
        assert result["error"] is not None
        assert "Test error" in result["error"]
    
    def test_run_phase_benchmark_timing(self):
        """Test that timing is accurate."""
        def delay_func():
            time.sleep(0.1)
            return "done"
        
        result = run_phase_benchmark("delay_phase", delay_func)
        
        assert result["duration_seconds"] >= 0.09  # Allow some tolerance

class TestBenchmarkReport:
    """Tests for benchmark report generation and saving."""
    
    def test_save_benchmark_report_creates_file(self, tmp_path):
        """Test that report file is created."""
        report = {
            "test": "data",
            "phases": []
        }
        
        # Temporarily change output directory
        original_output_dir = Path("data/processed")
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        
        try:
            save_path = save_benchmark_report(report)
            assert save_path.exists()
            
            with open(save_path, 'r') as f:
                loaded = json.load(f)
                assert loaded["test"] == "data"
        finally:
            # Clean up
            if Path("data/processed/benchmark_log.json").exists():
                Path("data/processed/benchmark_log.json").unlink()
    
    def test_run_full_benchmark_structure(self):
        """Test that full benchmark returns expected structure."""
        # Mock the phase functions to avoid actual execution
        with patch('benchmark.benchmark_parser_phase') as mock_parser, \
             patch('benchmark.benchmark_splitter') as mock_splitter, \
             patch('benchmark.benchmark_ablation_phase') as mock_ablation, \
             patch('benchmark.benchmark_classifier_phase') as mock_classifier, \
             patch('benchmark.benchmark_simulation_phase') as mock_simulation, \
             patch('benchmark.benchmark_stats_phase') as mock_stats:
            
            mock_parser.return_value = {"phase_name": "parser", "success": True}
            mock_splitter.return_value = {"phase_name": "splitter", "success": True}
            mock_ablation.return_value = {"phase_name": "ablation", "success": True}
            mock_classifier.return_value = {"phase_name": "classifier", "success": True}
            mock_simulation.return_value = {"phase_name": "simulation", "success": True}
            mock_stats.return_value = {"phase_name": "stats", "success": True}
            
            report = run_full_benchmark()
            
            assert "benchmark_start" in report
            assert "total_duration_seconds" in report
            assert "phases" in report
            assert "summary" in report
            assert "total_phases" in report["summary"]
            assert "success_rate" in report["summary"]
            assert "within_6_hour_limit" in report["summary"]
            
            assert len(report["phases"]) == 6

class TestMain:
    """Tests for main function."""
    
    def test_main_returns_report(self):
        """Test that main function returns a report."""
        with patch('benchmark.run_full_benchmark') as mock_run, \
             patch('benchmark.save_benchmark_report') as mock_save, \
             patch('builtins.print'):
            
            mock_run.return_value = {
                "total_duration_seconds": 100,
                "summary": {
                    "success_rate": 100.0,
                    "within_6_hour_limit": True
                }
            }
            mock_save.return_value = Path("data/processed/benchmark_log.json")
            
            result = main()
            
            assert result is not None
            assert "total_duration_seconds" in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
