"""
Unit tests for inclusion metrics calculation in process.py
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from src.data.process import calculate_and_save_inclusion_metrics

class TestInclusionMetrics:
    def test_calculate_and_save_metrics_success(self):
        """Test successful calculation and saving of inclusion metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "inclusion_metrics.json")
            
            # Call the function
            calculate_and_save_inclusion_metrics(
                total_games=100,
                parsed_games=98,
                output_path=output_path
            )
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            
            assert metrics["total_games"] == 100
            assert metrics["parsed_games"] == 98
            assert metrics["inclusion_rate"] == 0.98

    def test_calculate_and_save_metrics_zero_total(self):
        """Test handling of zero total games (avoid division by zero)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "inclusion_metrics.json")
            
            calculate_and_save_inclusion_metrics(
                total_games=0,
                parsed_games=0,
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            
            assert metrics["total_games"] == 0
            assert metrics["parsed_games"] == 0
            assert metrics["inclusion_rate"] == 0.0

    def test_calculate_and_save_metrics_all_parsed(self):
        """Test 100% inclusion rate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "inclusion_metrics.json")
            
            calculate_and_save_inclusion_metrics(
                total_games=50,
                parsed_games=50,
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                metrics = json.load(f)
            
            assert metrics["inclusion_rate"] == 1.0

    def test_calculate_and_save_metrics_creates_directory(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = os.path.join(tmpdir, "subdir", "nested")
            output_path = os.path.join(nested_dir, "inclusion_metrics.json")
            
            # Ensure the directory does not exist yet
            assert not os.path.exists(nested_dir)
            
            calculate_and_save_inclusion_metrics(
                total_games=10,
                parsed_games=10,
                output_path=output_path
            )
            
            assert os.path.exists(output_path)