"""
Unit tests for the parser module.
"""
import json
import tempfile
import os
import pytest
import pandas as pd
from pathlib import Path

# Import the module under test
from code.parser import parse_turn_data, extract_metrics_from_trajectory, parse_trajectories


class TestParseTurnData:
    """Tests for parse_turn_data function."""

    def test_valid_turn_json(self):
        """Test parsing valid turn JSON."""
        turn_json = json.dumps({
            "health": 100.0,
            "threat": 0.5,
            "deck_size": 30
        })
        result = parse_turn_data(turn_json)
        
        assert result is not None
        assert result["health"] == 100.0
        assert result["threat"] == 0.5
        assert result["deck_size"] == 30

    def test_missing_fields_returns_none(self):
        """Test that missing required fields return None."""
        turn_json = json.dumps({
            "health": 100.0,
            "threat": 0.5
            # missing deck_size
        })
        result = parse_turn_data(turn_json)
        assert result is None

    def test_empty_json_returns_none(self):
        """Test that empty JSON returns None."""
        assert parse_turn_data("") is None
        assert parse_turn_data(None) is None

    def test_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        assert parse_turn_data("not valid json") is None

    def test_string_numeric_conversion(self):
        """Test that string numeric values are converted correctly."""
        turn_json = json.dumps({
            "health": "100",
            "threat": "0.5",
            "deck_size": "30"
        })
        result = parse_turn_data(turn_json)
        
        assert result is not None
        assert isinstance(result["health"], float)
        assert isinstance(result["threat"], float)
        assert isinstance(result["deck_size"], int)


class TestExtractMetricsFromTrajectory:
    """Tests for extract_metrics_from_trajectory function."""

    def test_single_turn_trajectory(self):
        """Test extracting metrics from a single-turn trajectory."""
        row = pd.Series({
            "trajectory_id": "traj_001",
            "turns": json.dumps([{
                "health": 100.0,
                "threat": 0.5,
                "deck_size": 30
            }])
        })
        
        metrics = extract_metrics_from_trajectory(row)
        
        assert len(metrics) == 1
        assert metrics[0]["trajectory_id"] == "traj_001"
        assert metrics[0]["turn_index"] == 0
        assert metrics[0]["health"] == 100.0

    def test_multi_turn_trajectory(self):
        """Test extracting metrics from a multi-turn trajectory."""
        turns = [
            {"health": 100.0, "threat": 0.1, "deck_size": 30},
            {"health": 95.0, "threat": 0.3, "deck_size": 29},
            {"health": 90.0, "threat": 0.5, "deck_size": 28}
        ]
        row = pd.Series({
            "trajectory_id": "traj_002",
            "turns": json.dumps(turns)
        })
        
        metrics = extract_metrics_from_trajectory(row)
        
        assert len(metrics) == 3
        assert all(m["trajectory_id"] == "traj_002" for m in metrics)
        assert metrics[0]["turn_index"] == 0
        assert metrics[2]["turn_index"] == 2

    def test_empty_turns_list(self):
        """Test handling of empty turns list."""
        row = pd.Series({
            "trajectory_id": "traj_003",
            "turns": json.dumps([])
        })
        
        metrics = extract_metrics_from_trajectory(row)
        assert len(metrics) == 0

    def test_missing_turns_column(self):
        """Test handling of missing turns data."""
        row = pd.Series({
            "trajectory_id": "traj_004",
            "turns": None
        })
        
        metrics = extract_metrics_from_trajectory(row)
        assert len(metrics) == 0


class TestParseTrajectories:
    """Integration tests for parse_trajectories function."""

    def test_parse_valid_csv(self, tmp_path):
        """Test parsing a valid CSV file."""
        # Create test data
        test_data = {
            "trajectory_id": ["traj_001", "traj_002"],
            "turns": [
                json.dumps([{"health": 100.0, "threat": 0.5, "deck_size": 30}]),
                json.dumps([
                    {"health": 100.0, "threat": 0.1, "deck_size": 30},
                    {"health": 95.0, "threat": 0.3, "deck_size": 29}
                ])
            ]
        }
        df = pd.DataFrame(test_data)
        
        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        result_df = parse_trajectories(str(input_path), str(output_path))
        
        assert len(result_df) == 3  # 1 + 2 turns
        assert result_df["trajectory_id"].nunique() == 2
        assert os.path.exists(output_path)

    def test_missing_input_file(self, tmp_path):
        """Test error handling for missing input file."""
        input_path = tmp_path / "nonexistent.csv"
        output_path = tmp_path / "output.csv"
        
        with pytest.raises(FileNotFoundError):
            parse_trajectories(str(input_path), str(output_path))

    def test_missing_turns_column(self, tmp_path):
        """Test error handling for missing turns column."""
        test_data = {
            "trajectory_id": ["traj_001"],
            "other_column": ["value"]
        }
        df = pd.DataFrame(test_data)
        
        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError):
            parse_trajectories(str(input_path), str(output_path))

    def test_mixed_valid_invalid_turns(self, tmp_path):
        """Test handling of mixed valid and invalid turn data."""
        test_data = {
            "trajectory_id": ["traj_001", "traj_002"],
            "turns": [
                json.dumps([{"health": 100.0, "threat": 0.5, "deck_size": 30}]),
                json.dumps([
                    {"health": 100.0, "threat": 0.1, "deck_size": 30},
                    {"health": "invalid", "threat": 0.3, "deck_size": 29}  # Invalid health
                ])
            ]
        }
        df = pd.DataFrame(test_data)
        
        input_path = tmp_path / "input.csv"
        output_path = tmp_path / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        result_df = parse_trajectories(str(input_path), str(output_path))
        
        # Should only include valid turns
        assert len(result_df) == 2  # 1 from first traj, 1 valid from second