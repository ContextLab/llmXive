"""
Unit tests for scaling simulation in run_experiment.py
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import csv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from run_experiment import parse_agent_counts, GameResult, save_results

class TestScalingSimulation:
    """Tests for scaling simulation functionality."""
    
    def test_parse_agent_counts_single(self):
        """Test parsing single agent count."""
        result = parse_agent_counts("5")
        assert result == [5]
    
    def test_parse_agent_counts_multiple(self):
        """Test parsing multiple agent counts."""
        result = parse_agent_counts("3,5,7")
        assert result == [3, 5, 7]
    
    def test_parse_agent_counts_default(self):
        """Test default agent count."""
        result = parse_agent_counts("")
        assert result == [5]
    
    def test_save_results_creates_file(self):
        """Test that save_results creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.csv")
            
            results = [
                GameResult(
                    game_id=1,
                    context_condition='scaling',
                    agent_count=3,
                    specialization_index=1.5,
                    retrieval_efficiency=0.8,
                    success=True,
                    duration=0.1
                ),
                GameResult(
                    game_id=2,
                    context_condition='scaling',
                    agent_count=5,
                    specialization_index=2.0,
                    retrieval_efficiency=0.75,
                    success=True,
                    duration=0.15
                )
            ]
            
            save_results(results, output_path)
            
            assert os.path.exists(output_path)
            
            # Verify CSV content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['agent_count'] == '3'
                assert rows[1]['agent_count'] == '5'
    
    def test_save_results_creates_directory(self):
        """Test that save_results creates directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "subdir", "test_results.csv")
            
            results = [
                GameResult(
                    game_id=1,
                    context_condition='scaling',
                    agent_count=7,
                    specialization_index=1.8,
                    retrieval_efficiency=0.85,
                    success=True,
                    duration=0.12
                )
            ]
            
            save_results(results, output_path)
            
            assert os.path.exists(output_path)
            assert os.path.exists(os.path.join(tmpdir, "subdir"))