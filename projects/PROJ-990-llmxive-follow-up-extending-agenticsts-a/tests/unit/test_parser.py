"""
Unit tests for code/parser.py (T006a)
"""
import os
import sys
import json
import math
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.parser import (
    extract_move_entropy,
    validate_trajectory_against_schema,
    extract_metrics_from_trajectory,
    validate_data_source,
    main
)

class TestExtractMoveEntropy:
    def test_empty_list(self):
        assert math.isnan(extract_move_entropy([]))

    def test_single_move(self):
        assert extract_move_entropy(["move_a"]) == 0.0

    def test_two_moves(self):
        # log2(2) = 1.0
        assert extract_move_entropy(["move_a", "move_b"]) == 1.0

    def test_four_moves(self):
        # log2(4) = 2.0
        assert extract_move_entropy(["a", "b", "c", "d"]) == 2.0

class TestValidateTrajectoryAgainstSchema:
    def test_valid_trajectory(self):
        schema = {
            "required": ["trajectory_id", "turns"],
            "properties": {
                "trajectory_id": {"type": "string"},
                "turns": {"type": "array"}
            }
        }
        trajectory = {"trajectory_id": "123", "turns": []}
        assert validate_trajectory_against_schema(trajectory, schema) is True

    def test_missing_required_field(self):
        schema = {
            "required": ["trajectory_id"],
            "properties": {}
        }
        trajectory = {"turns": []}
        with pytest.raises(ValueError, match="Missing required field 'trajectory_id'"):
            validate_trajectory_against_schema(trajectory, schema)

    def test_type_mismatch(self):
        schema = {
            "required": [],
            "properties": {
                "score": {"type": "integer"}
            }
        }
        trajectory = {"score": "not_an_int"}
        with pytest.raises(ValueError, match="expected integer"):
            validate_trajectory_against_schema(trajectory, schema)

class TestExtractMetricsFromTrajectory:
    def test_basic_extraction(self):
        trajectory = {
            "trajectory_id": "test_001",
            "layer_name": "layer_1",
            "turns": [
                {
                    "health_ratio": 0.8,
                    "enemy_threat": 0.2,
                    "deck_size": 10,
                    "legal_moves": ["a", "b"]
                },
                {
                    "health_ratio": 0.5,
                    "enemy_threat": 0.5,
                    "deck_size": 9,
                    "legal_moves": ["c"]
                }
            ]
        }
        metrics = list(extract_metrics_from_trajectory(trajectory))
        
        assert len(metrics) == 2
        assert metrics[0]["trajectory_id"] == "test_001"
        assert metrics[0]["turn"] == 0
        assert metrics[0]["health_ratio"] == 0.8
        assert metrics[0]["move_entropy"] == 1.0 # log2(2)
        
        assert metrics[1]["turn"] == 1
        assert metrics[1]["move_entropy"] == 0.0 # log2(1)

    def test_missing_turns(self):
        trajectory = {
            "trajectory_id": "test_002",
            "layer_name": "layer_2"
            # No turns key
        }
        metrics = list(extract_metrics_from_trajectory(trajectory))
        assert len(metrics) == 0

    def test_empty_turns_list(self):
        trajectory = {
            "trajectory_id": "test_003",
            "layer_name": "layer_2",
            "turns": []
        }
        metrics = list(extract_metrics_from_trajectory(trajectory))
        assert len(metrics) == 0

class TestValidateDataSource:
    def test_file_exists(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"{}")
            tmp_path = Path(tmp.name)
        
        try:
            validate_data_source(tmp_path) # Should not raise
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        fake_path = Path("/nonexistent/path/file.jsonl")
        with pytest.raises(FileNotFoundError):
            validate_data_source(fake_path)

    def test_file_empty(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Write nothing
            tmp_path = Path(tmp.name)
        
        try:
            with pytest.raises(FileNotFoundError, match="empty"):
                validate_data_source(tmp_path)
        finally:
            os.unlink(tmp_path)
