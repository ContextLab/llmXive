"""
Tests for token budget logging functionality in simulator.py (T056).
"""
import os
import json
import csv
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from simulator import (
    estimate_layer_tokens,
    calculate_total_tokens,
    prune_layers_for_budget,
    enforce_minimum_context,
    generate_token_budget_detailed_csv,
    run_dynamic_simulation
)

class TestTokenEstimation:
    def test_estimate_layer_tokens_empty(self):
        assert estimate_layer_tokens({}) == 0
        assert estimate_layer_tokens(None) == 0

    def test_estimate_layer_tokens_simple(self):
        layer = {"content": "test"}
        tokens = estimate_layer_tokens(layer)
        assert tokens > 0
        assert isinstance(tokens, int)

class TestTokenPruning:
    def test_no_pruning_needed(self):
        layers = [{"content": "small"}]
        result, pruned, reason = prune_layers_for_budget(layers, 10000)
        assert len(result) == 1
        assert len(pruned) == 0
        assert "No pruning needed" in reason

    def test_pruning_with_utility(self):
        layers = [
            {"content": "important"},
            {"content": "less_important"},
            {"content": "unimportant"}
        ]
        utilities = [0.9, 0.5, 0.1]
        
        result, pruned, reason = prune_layers_for_budget(
            layers, 10, utilities
        )
        assert len(result) <= len(layers)
        assert reason == "Token budget exceeded" or len(result) == len(layers)

class TestMinimumContext:
    def test_floor_not_applied(self):
        layers = [{"content": "x" * 1000}]
        result, applied = enforce_minimum_context(layers, 100)
        assert not applied

    def test_floor_applied(self):
        layers = [{"content": "x" * 10}]
        result, applied = enforce_minimum_context(layers, 1000)
        assert applied
        assert len(result) > len(layers)

class TestTokenBudgetCSV:
    @pytest.fixture
    def temp_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_token_budget.csv"

    @patch('simulator.load_raw_trajectory')
    def test_generate_csv_with_mock_data(self, mock_load, temp_output_path):
        # Setup mock data
        mock_load.return_value = {
            "trajectory_id": "test_001",
            "layers": [
                {"content": "layer1_content" * 100},
                {"content": "layer2_content" * 100},
                {"content": "layer3_content" * 100}
            ]
        }

        result_path = generate_token_budget_detailed_csv(
            trajectory_ids=["test_001"],
            output_path=temp_output_path,
            mode="dynamic"
        )

        # Verify file exists
        assert result_path.exists()

        # Verify CSV structure
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            row = rows[0]
            
            # Check required columns
            assert "trajectory_id" in row
            assert "initial_tokens" in row
            assert "selected_layers" in row
            assert "final_tokens" in row
            assert "layers_pruned" in row
            assert "pruning_reason" in row

            # Verify data types
            assert int(row["initial_tokens"]) >= 0
            assert int(row["final_tokens"]) >= 0

    @patch('simulator.load_raw_trajectory')
    def test_multiple_trajectories(self, mock_load, temp_output_path):
        mock_load.return_value = {
            "trajectory_id": "test_001",
            "layers": [{"content": "x" * 100}]
        }

        result_path = generate_token_budget_detailed_csv(
            trajectory_ids=["test_001", "test_002", "test_003"],
            output_path=temp_output_path,
            mode="dynamic"
        )

        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3

    def test_empty_trajectory_list(self, temp_output_path):
        result_path = generate_token_budget_detailed_csv(
            trajectory_ids=[],
            output_path=temp_output_path,
            mode="dynamic"
        )
        
        assert result_path.exists()
        with open(result_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0

class TestDynamicSimulation:
    @patch('simulator.load_raw_trajectory')
    def test_run_dynamic_simulation(self, mock_load):
        mock_load.return_value = {
            "trajectory_id": "test_001",
            "layers": [
                {"content": "x" * 100},
                {"content": "y" * 100}
            ]
        }

        result = run_dynamic_simulation("test_001")

        assert "trajectory_id" in result
        assert "initial_tokens" in result
        assert "final_tokens" in result
        assert "selected_layers" in result
        assert "layers_pruned" in result
        assert "pruning_reason" in result
        assert isinstance(result["initial_tokens"], int)
        assert isinstance(result["final_tokens"], int)
        assert result["final_tokens"] <= result["initial_tokens"]