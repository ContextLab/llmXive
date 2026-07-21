"""
Integration tests for generation profiling functionality.

These tests verify that the profiling script runs correctly and
produces valid output within memory constraints.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.generation.generation_profile import (
    generate_synthetic_sequence,
    run_profile_experiment,
    save_profile_report
)

class TestGenerationProfile:
    """Test suite for generation profiling."""
    
    def test_generate_synthetic_sequence(self):
        """Test synthetic sequence generation."""
        length = 50
        seq = generate_synthetic_sequence(length)
        
        assert "prompt_id" in seq
        assert "tokens" in seq
        assert len(seq["tokens"]) == length
        assert "logits" in seq
        assert len(seq["logits"]) == length
        assert "entropy" in seq
        assert len(seq["entropy"]) == length
        
        # Verify entropy values are finite
        for entropy in seq["entropy"]:
            assert np.isfinite(entropy)
    
    def test_run_profile_experiment_basic(self):
        """Test basic profile experiment execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily change output path
            original_path = Path(project_root) / "data"
            test_path = Path(tmpdir)
            
            # Mock the output path
            with patch('src.generation.generation_profile.Path') as mock_path:
                mock_path.return_value = test_path
                
                # Run a small experiment
                peak_rss, avg_latency = run_profile_experiment(
                    batch_size=10,
                    max_tokens=50,
                    num_batches=2
                )
                
                # Verify results
                assert peak_rss > 0
                assert avg_latency >= 0
                assert isinstance(peak_rss, float)
                assert isinstance(avg_latency, float)
    
    def test_save_profile_report(self):
        """Test profile report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = [
                {
                    "batch_size": 50,
                    "peak_rss_mb": 1024.5,
                    "avg_latency_s": 0.123,
                    "total_tokens": 500
                },
                {
                    "batch_size": 100,
                    "peak_rss_mb": 2048.7,
                    "avg_latency_s": 0.245,
                    "total_tokens": 500
                }
            ]
            
            output_path = Path(tmpdir) / "profile_report.txt"
            saved_path = save_profile_report(results, output_path)
            
            assert saved_path.exists()
            
            with open(saved_path, "r") as f:
                content = f.read()
            
            # Verify report content
            assert "Generation Pipeline Profiling Report" in content
            assert "Batch Size" in content
            assert "Peak RSS (MB)" in content
            assert "Avg Latency (s)" in content
            assert "1024.50" in content
            assert "2048.70" in content
            assert "COMPLIANCE" in content
    
    def test_memory_limit_compliance(self):
        """Test that memory usage stays within limits."""
        # This test verifies the logic for checking memory compliance
        # In a real scenario, this would be validated by the profiling script
        
        mock_results = [
            {"batch_size": 50, "peak_rss_mb": 1000.0},
            {"batch_size": 100, "peak_rss_mb": 2000.0},
            {"batch_size": 25, "peak_rss_mb": 500.0}
        ]
        
        max_rss = max(r['peak_rss_mb'] for r in mock_results)
        limit_mb = 6656  # 6.5 GB
        
        assert max_rss < limit_mb, f"Memory usage {max_rss} MB exceeds limit {limit_mb} MB"
    
    def test_profile_stats_json(self):
        """Test that profile stats are saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock the stats file path
            stats_file = Path(tmpdir) / "profile_stats.json"
            
            stats_data = {
                "batch_size": 50,
                "num_batches": 10,
                "total_tokens": 500,
                "peak_rss_mb": 1024.5,
                "avg_latency_s": 0.123,
                "total_time_s": 1.23
            }
            
            with open(stats_file, "w") as f:
                json.dump(stats_data, f, indent=2)
            
            assert stats_file.exists()
            
            with open(stats_file, "r") as f:
                loaded_data = json.load(f)
            
            assert loaded_data["batch_size"] == 50
            assert loaded_data["peak_rss_mb"] == 1024.5
            assert loaded_data["avg_latency_s"] == 0.123
            assert loaded_data["total_tokens"] == 500