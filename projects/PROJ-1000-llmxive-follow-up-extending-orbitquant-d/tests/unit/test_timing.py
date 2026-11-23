"""
Unit tests for the timing module.

Tests:
    - load_prompts_for_timing
    - compute_statistics
    - save_timing_results
"""

import os
import sys
import json
import tempfile
import csv
from pathlib import Path

import pytest
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evaluation.timing import (
    load_prompts_for_timing,
    compute_statistics,
    save_timing_results
)

class TestLoadPromptsForTiming:
    """Tests for load_prompts_for_timing function."""
    
    def test_load_prompts_success(self, tmp_path):
        """Test loading prompts from a valid CSV file."""
        # Create a temporary CSV file
        csv_file = tmp_path / "prompts.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt'])
            writer.writeheader()
            writer.writerow({'prompt': 'A beautiful sunset'})
            writer.writerow({'prompt': 'A mountain landscape'})
            writer.writerow({'prompt': 'An abstract painting'})
        
        prompts = load_prompts_for_timing(str(csv_file))
        
        assert len(prompts) == 3
        assert prompts[0] == 'A beautiful sunset'
        assert prompts[1] == 'A mountain landscape'
        assert prompts[2] == 'An abstract painting'
    
    def test_load_prompts_with_max_samples(self, tmp_path):
        """Test loading prompts with max_samples limit."""
        csv_file = tmp_path / "prompts.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt'])
            writer.writeheader()
            for i in range(10):
                writer.writerow({'prompt': f'Prompt {i}'})
        
        prompts = load_prompts_for_timing(str(csv_file), max_samples=5)
        
        assert len(prompts) == 5
        assert prompts[0] == 'Prompt 0'
        assert prompts[-1] == 'Prompt 4'
    
    def test_load_prompts_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_prompts_for_timing("/nonexistent/path.csv")
    
    def test_load_prompts_empty_file(self, tmp_path):
        """Test that ValueError is raised for empty CSV."""
        csv_file = tmp_path / "empty.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt'])
            writer.writeheader()
        
        with pytest.raises(ValueError):
            load_prompts_for_timing(str(csv_file))

class TestComputeStatistics:
    """Tests for compute_statistics function."""
    
    def test_compute_statistics_basic(self):
        """Test basic statistics computation."""
        timings = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = compute_statistics(timings)
        
        assert stats["mean"] == 3.0
        assert stats["median"] == 3.0
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["count"] == 5
        assert abs(stats["std"] - 1.4142135623730951) < 1e-5
    
    def test_compute_statistics_single_value(self):
        """Test statistics with a single value."""
        timings = [5.0]
        stats = compute_statistics(timings)
        
        assert stats["mean"] == 5.0
        assert stats["median"] == 5.0
        assert stats["std"] == 0.0
        assert stats["count"] == 1
    
    def test_compute_statistics_empty_list(self):
        """Test statistics with an empty list."""
        stats = compute_statistics([])
        
        assert stats == {}

class TestSaveTimingResults:
    """Tests for save_timing_results function."""
    
    def test_save_timing_results(self, tmp_path):
        """Test saving timing results to JSON."""
        output_file = tmp_path / "timing_results.json"
        
        static_timings = [0.1, 0.2, 0.3]
        dynamic_timings = [0.15, 0.25, 0.35]
        
        save_timing_results(static_timings, dynamic_timings, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            results = json.load(f)
        
        assert "static" in results
        assert "dynamic" in results
        assert "comparison" in results
        
        assert len(results["static"]["timings"]) == 3
        assert len(results["dynamic"]["timings"]) == 3
        assert "statistics" in results["static"]
        assert "statistics" in results["dynamic"]
        
        # Check comparison
        assert results["comparison"]["overhead_ratio"] is not None
        assert results["comparison"]["absolute_overhead"] is not None
    
    def test_save_creates_directories(self, tmp_path):
        """Test that save_timing_results creates parent directories."""
        nested_file = tmp_path / "nested" / "deep" / "timing_results.json"
        
        static_timings = [0.1]
        dynamic_timings = [0.15]
        
        save_timing_results(static_timings, dynamic_timings, str(nested_file))
        
        assert nested_file.exists()