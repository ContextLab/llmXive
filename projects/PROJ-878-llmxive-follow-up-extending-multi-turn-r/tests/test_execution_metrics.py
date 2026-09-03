"""
Tests for T024: Execution Metrics Calculation (Divergence from Ground Truth).
"""
import os
import json
import csv
import tempfile
import pytest
from pathlib import Path
from typing import Dict, List, Any

# Import the functions to test
# We assume the test is run from the project root or code/tests
# Adjust import path if necessary
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from execution_metrics import jaccard_distance, calculate_divergence_metrics, load_puzzles_metadata, load_execution_log

class TestJaccardDistance:
    """Unit tests for the Jaccard distance calculation."""
    
    def test_identical_paths(self):
        """Identical paths should have distance 0."""
        path = ["A", "B", "C"]
        assert jaccard_distance(path, path) == 0.0
        assert jaccard_distance(["A"], ["A"]) == 0.0
    
    def test_disjoint_paths(self):
        """Disjoint paths should have distance 1.0."""
        assert jaccard_distance(["A", "B"], ["C", "D"]) == 1.0
    
    def test_partial_overlap(self):
        """Partial overlap should be between 0 and 1."""
        # Intersection: {A}, Union: {A, B, C} -> 1/3
        # Distance = 1 - 1/3 = 2/3
        dist = jaccard_distance(["A", "B"], ["A", "C"])
        assert abs(dist - 0.6666666666666666) < 1e-9
    
    def test_empty_paths(self):
        """Both empty should be 0."""
        assert jaccard_distance([], []) == 0.0
    
    def test_one_empty(self):
        """One empty, one not should be 1.0."""
        assert jaccard_distance(["A"], []) == 1.0
        assert jaccard_distance([], ["A"]) == 1.0

class TestLoadPuzzlesMetadata:
    """Tests for loading puzzle metadata."""
    
    def test_load_valid_jsonl(self):
        """Should load a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"instance_id": "1", "ground_truth_path": ["A", "B"]}) + "\n")
            f.write(json.dumps({"instance_id": "2", "ground_truth_path": ["C", "D"]}) + "\n")
            path = f.name
        
        try:
            data = load_puzzles_metadata(path)
            assert len(data) == 2
            assert data["1"]["ground_truth_path"] == ["A", "B"]
            assert data["2"]["ground_truth_path"] == ["C", "D"]
        finally:
            os.unlink(path)
    
    def test_missing_file(self):
        """Should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_puzzles_metadata("/nonexistent/path.jsonl")

class TestLoadExecutionLog:
    """Tests for loading execution log."""
    
    def test_load_valid_csv(self):
        """Should load a valid CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("instance_id,predicted_path,turns\n")
            f.write("1,[\"A\",\"B\"],5\n")
            f.write("2,[\"C\"],10\n")
            path = f.name
        
        try:
            data = load_execution_log(path)
            assert len(data) == 2
            assert data[0]["predicted_path"] == ["A", "B"]
            assert data[1]["predicted_path"] == ["C"]
        finally:
            os.unlink(path)
    
    def test_missing_file(self):
        """Should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_execution_log("/nonexistent/path.csv")

class TestCalculateDivergenceMetrics:
    """Integration tests for the full calculation pipeline."""
    
    def test_full_pipeline(self):
        """Test the full calculation pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock puzzle metadata
            puzzle_path = os.path.join(tmpdir, "puzzles.jsonl")
            with open(puzzle_path, 'w') as f:
                f.write(json.dumps({"instance_id": "1", "ground_truth_path": ["A", "B", "C"]}) + "\n")
                f.write(json.dumps({"instance_id": "2", "ground_truth_path": ["X", "Y"]}) + "\n")
                # Instance 3 has no ground truth in metadata (edge case)
                f.write(json.dumps({"instance_id": "3", "ground_truth_path": ["Z"]}) + "\n")
            
            # Create mock execution log
            log_path = os.path.join(tmpdir, "execution_log.csv")
            with open(log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["instance_id", "predicted_path", "turns"])
                writer.writerow(["1", '["A", "B"]', "5"])  # Partial match with GT
                writer.writerow(["2", '["Z"]', "10"])     # No match with GT
                writer.writerow(["4", '["A"]', "2"])      # Missing in metadata
            
            output_path = os.path.join(tmpdir, "output.csv")
            
            calculate_divergence_metrics(log_path, puzzle_path, output_path)
            
            # Verify output
            assert os.path.exists(output_path)
            with open(output_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3
            
            # Row 1: GT ["A","B","C"], Pred ["A","B"] -> Intersection {A,B}, Union {A,B,C} -> 1 - 2/3 = 0.333
            row1 = next(r for r in rows if r['instance_id'] == '1')
            assert abs(float(row1['divergence_from_ground_truth']) - 0.3333333333333333) < 1e-6
            
            # Row 2: GT ["X","Y"], Pred ["Z"] -> Disjoint -> 1.0
            row2 = next(r for r in rows if r['instance_id'] == '2')
            assert float(row2['divergence_from_ground_truth']) == 1.0
            
            # Row 4: Missing in metadata -> 1.0
            row4 = next(r for r in rows if r['instance_id'] == '4')
            assert float(row4['divergence_from_ground_truth']) == 1.0
    
    def test_missing_metadata_raises(self):
        """Should raise FileNotFoundError if metadata is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "log.csv")
            with open(log_path, 'w') as f:
                f.write("instance_id,predicted_path\n")
                f.write("1,[]\n")
            
            output_path = os.path.join(tmpdir, "out.csv")
            
            with pytest.raises(FileNotFoundError):
                calculate_divergence_metrics(log_path, "/nonexistent.jsonl", output_path)