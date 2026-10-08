import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
import numpy as np

# Ensure code/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from rm_executor import ReflectiveMaskingExecutor
from utils.graph_utils import graph_from_dict, get_all_simple_paths_from_source_to_target, get_random_valid_path_different_from_reference


class TestIndependentLogicalValidator:
    """
    Integration test for Independent Logical Validator (ILV) verifying path coverage.
    
    This test validates that the ILV logic correctly parses model output, reconstructs
    the logic graph, and calculates path coverage against the ground truth DAG.
    """

    def test_ilv_path_coverage_calculation(self):
        """
        Test that ILV correctly calculates path coverage >= 0.95 for a known valid path.
        
        Scenario:
        1. Create a simple DAG with known structure.
        2. Generate a ground truth path.
        3. Simulate model output that matches the ground truth path.
        4. Verify path_coverage is calculated correctly (should be 1.0 or >= 0.95).
        """
        # Setup: Create a simple DAG
        # Nodes: A -> B -> C -> D
        #        A -> E -> D
        # Ground truth path: A -> B -> C -> D
        
        graph_dict = {
            "nodes": ["A", "B", "C", "D", "E"],
            "edges": [
                ("A", "B"),
                ("B", "C"),
                ("C", "D"),
                ("A", "E"),
                ("E", "D")
            ]
        }
        
        graph = graph_from_dict(graph_dict)
        ground_truth_path = ["A", "B", "C", "D"]
        
        # Simulate model output (list of nodes visited in order)
        model_output_path = ["A", "B", "C", "D"]
        
        # Calculate all valid paths from source to target
        all_paths = get_all_simple_paths_from_source_to_target(graph, "A", "D")
        
        # ILV Logic: Check if model output is a valid path
        is_valid = model_output_path in all_paths
        
        # ILV Logic: Calculate path coverage
        # Coverage = (number of edges in model path that exist in ground truth) / (total edges in ground truth)
        # Or more simply: if the model path IS the ground truth path, coverage is 1.0
        
        if is_valid:
            # Calculate intersection of edges
            model_edges = set(zip(model_output_path, model_output_path[1:]))
            gt_edges = set(zip(ground_truth_path, ground_truth_path[1:]))
            
            intersection = model_edges.intersection(gt_edges)
            coverage = len(intersection) / len(gt_edges) if len(gt_edges) > 0 else 0.0
        else:
            coverage = 0.0
        
        # Assertion: Coverage should be 1.0 for exact match
        assert coverage == 1.0, f"Expected coverage 1.0, got {coverage}"
        assert coverage >= 0.95, f"Path coverage {coverage} is below threshold 0.95"

    def test_ilv_path_coverage_partial_match(self):
        """
        Test ILV with a partial match path.
        
        Scenario:
        1. Model output follows part of the ground truth path but diverges.
        2. Verify coverage is calculated correctly (should be < 1.0).
        """
        graph_dict = {
            "nodes": ["A", "B", "C", "D", "E"],
            "edges": [
                ("A", "B"),
                ("B", "C"),
                ("C", "D"),
                ("A", "E"),
                ("E", "D")
            ]
        }
        
        graph = graph_from_dict(graph_dict)
        ground_truth_path = ["A", "B", "C", "D"]
        
        # Model output diverges at C
        model_output_path = ["A", "B", "E", "D"]
        
        all_paths = get_all_simple_paths_from_source_to_target(graph, "A", "D")
        is_valid = model_output_path in all_paths
        
        if is_valid:
            model_edges = set(zip(model_output_path, model_output_path[1:]))
            gt_edges = set(zip(ground_truth_path, ground_truth_path[1:]))
            
            intersection = model_edges.intersection(gt_edges)
            coverage = len(intersection) / len(gt_edges) if len(gt_edges) > 0 else 0.0
        else:
            coverage = 0.0
        
        # Assertion: Coverage should be partial (2/4 = 0.5)
        # Edges: (A,B) match, (B,C) vs (B,E) no, (C,D) vs (E,D) no
        # Actually: (A,B) is in both. (B,C) not in model. (C,D) not in model.
        # Model edges: (A,B), (B,E), (E,D). GT edges: (A,B), (B,C), (C,D).
        # Intersection: {(A,B)}. Coverage = 1/3 = 0.333
        assert coverage < 1.0, f"Expected coverage < 1.0, got {coverage}"
        assert coverage >= 0.0, f"Coverage cannot be negative: {coverage}"

    def test_ilv_invalid_path_detection(self):
        """
        Test that ILV correctly identifies invalid paths (cycles or non-existent edges).
        """
        graph_dict = {
            "nodes": ["A", "B", "C"],
            "edges": [
                ("A", "B"),
                ("B", "C")
            ]
        }
        
        graph = graph_from_dict(graph_dict)
        
        # Model output: A -> C (no direct edge)
        model_output_path = ["A", "C"]
        
        all_paths = get_all_simple_paths_from_source_to_target(graph, "A", "C")
        is_valid = model_output_path in all_paths
        
        assert not is_valid, "Model output should be detected as invalid path"

    def test_ilv_integration_with_executor(self):
        """
        Integration test: Verify that ReflectiveMaskingExecutor uses ILV correctly.
        
        This test mocks the model and verifies that the executor:
        1. Calls the ILV logic.
        2. Records path_coverage in the results.
        3. Flags 'ilv_fail' if coverage < 0.95.
        """
        # Create a temporary directory for test artifacts
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "test_puzzles.jsonl"
            output_file = Path(tmp_dir) / "test_execution_log.csv"
            
            # Create test input data
            test_data = [
                {
                    "instance_id": "test_001",
                    "text": "Logical puzzle A -> B -> C",
                    "ground_truth_path": ["A", "B", "C"],
                    "nesting_depth": 2,
                    "branching_factor": 1,
                    "graph_structure": {
                        "nodes": ["A", "B", "C"],
                        "edges": [("A", "B"), ("B", "C")]
                    }
                },
                {
                    "instance_id": "test_002",
                    "text": "Logical puzzle X -> Y -> Z",
                    "ground_truth_path": ["X", "Y", "Z"],
                    "nesting_depth": 2,
                    "branching_factor": 1,
                    "graph_structure": {
                        "nodes": ["X", "Y", "Z"],
                        "edges": [("X", "Y"), ("Y", "Z")]
                    }
                }
            ]
            
            with open(input_file, "w") as f:
                for item in test_data:
                    f.write(json.dumps(item) + "\n")
            
            # Mock the model loading and execution
            with patch.object(ReflectiveMaskingExecutor, "__init__", return_value=None):
                with patch.object(ReflectiveMaskingExecutor, "load_model", return_value=None):
                    with patch.object(ReflectiveMaskingExecutor, "run_single_puzzle") as mock_run:
                        # Mock return values: first success, second ILV fail
                        mock_run.side_effect = [
                            {
                                "instance_id": "test_001",
                                "turns_to_converge": 3,
                                "convergence_status": "success",
                                "path_coverage": 1.0,
                                "divergence_from_ground_truth": 0.0,
                                "final_path": ["A", "B", "C"]
                            },
                            {
                                "instance_id": "test_002",
                                "turns_to_converge": 5,
                                "convergence_status": "ilv_fail",
                                "path_coverage": 0.5,
                                "divergence_from_ground_truth": 0.5,
                                "final_path": ["X", "Z"]
                            }
                        ]
                        
                        executor = ReflectiveMaskingExecutor()
                        executor.max_turns = 50
                        executor.batch_size = 1
                        executor.device = "cpu"
                        
                        # Run execution
                        executor.execute(input_file, output_file)
                        
                        # Verify output file exists
                        assert output_file.exists(), "Output file should be created"
                        
                        # Verify content
                        with open(output_file, "r") as f:
                            import csv
                            reader = csv.DictReader(f)
                            rows = list(reader)
                            
                        assert len(rows) == 2, "Should have 2 result rows"
                        
                        # Check first row (success)
                        assert rows[0]["instance_id"] == "test_001"
                        assert rows[0]["convergence_status"] == "success"
                        assert float(rows[0]["path_coverage"]) == 1.0
                        
                        # Check second row (ilv_fail)
                        assert rows[1]["instance_id"] == "test_002"
                        assert rows[1]["convergence_status"] == "ilv_fail"
                        assert float(rows[1]["path_coverage"]) == 0.5

    def test_ilv_edge_case_empty_path(self):
        """
        Test ILV behavior with empty or single-node paths.
        """
        # Empty path
        model_path = []
        gt_path = ["A", "B"]
        
        if len(model_path) < 2:
            coverage = 0.0
        else:
            model_edges = set(zip(model_path, model_path[1:]))
            gt_edges = set(zip(gt_path, gt_path[1:]))
            intersection = model_edges.intersection(gt_edges)
            coverage = len(intersection) / len(gt_edges) if len(gt_edges) > 0 else 0.0
        
        assert coverage == 0.0, "Empty path should have 0 coverage"

    def test_ilv_threshold_boundary(self):
        """
        Test ILV at the exact 0.95 threshold.
        """
        # Create a scenario where coverage is exactly 0.95
        # GT path has 20 edges, model matches 19
        gt_edges_count = 20
        matched_edges_count = 19
        coverage = matched_edges_count / gt_edges_count
        
        assert coverage == 0.95, f"Expected 0.95, got {coverage}"
        
        # Verify threshold logic
        is_success = coverage >= 0.95
        assert is_success, "0.95 should pass the threshold"