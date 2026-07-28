"""
Unit tests for T022: generate_baseline_comparison.py
"""

import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_baseline_comparison import load_simulation_data, generate_baseline_comparison

class TestLoadSimulationData:
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON simulation log."""
        data = [
            {"trajectory_id": "1", "win": True, "tokens_used": 100},
            {"trajectory_id": "2", "win": False, "tokens_used": 200},
            {"trajectory_id": "3", "win": True, "tokens_used": 150}
        ]
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        df = load_simulation_data(str(file_path))
        assert len(df) == 3
        assert list(df.columns) == ["trajectory_id", "win", "tokens_used"]
        assert df['win'].dtype == bool

    def test_load_missing_file(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_simulation_data(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_schema(self, tmp_path):
        """Test that missing columns raise ValueError."""
        data = [
            {"trajectory_id": "1", "win": True}  # Missing tokens_used
        ]
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)

        with pytest.raises(ValueError):
            load_simulation_data(str(file_path))

class TestGenerateBaselineComparison:
    def test_generate_csv(self, tmp_path):
        """Test that the function generates the correct CSV output."""
        # Create input data
        dynamic_data = [
            {"trajectory_id": "d1", "win": True, "tokens_used": 100},
            {"trajectory_id": "d2", "win": True, "tokens_used": 200},
        ]
        static_data = [
            {"trajectory_id": "s1", "win": False, "tokens_used": 300},
            {"trajectory_id": "s2", "win": True, "tokens_used": 400},
        ]
        random_data = [
            {"trajectory_id": "r1", "win": False, "tokens_used": 500},
            {"trajectory_id": "r2", "win": False, "tokens_used": 600},
        ]

        dynamic_path = tmp_path / "dynamic.json"
        static_path = tmp_path / "static.json"
        random_path = tmp_path / "random.json"
        output_path = tmp_path / "comparison.csv"

        with open(dynamic_path, 'w') as f:
            json.dump(dynamic_data, f)
        with open(static_path, 'w') as f:
            json.dump(static_data, f)
        with open(random_path, 'w') as f:
            json.dump(random_data, f)

        generate_baseline_comparison(
            str(dynamic_path),
            str(static_path),
            str(random_path),
            str(output_path)
        )

        # Verify output
        assert output_path.exists()
        df = pd.read_csv(output_path)
        assert 'condition' in df.columns
        assert 'win_rate' in df.columns
        assert 'avg_tokens' in df.columns
        assert 'std_dev_tokens' in df.columns
        assert len(df) == 3  # 3 conditions
        assert set(df['condition']) == {'dynamic', 'static', 'random'}

        # Check dynamic win_rate (2 wins out of 2 = 1.0)
        dynamic_row = df[df['condition'] == 'dynamic'].iloc[0]
        assert dynamic_row['win_rate'] == 1.0
        assert dynamic_row['avg_tokens'] == 150.0  # (100+200)/2

    def test_missing_input_files(self, tmp_path):
        """Test that missing input files raise an error."""
        output_path = tmp_path / "comparison.csv"
        # Only create one file
        dynamic_path = tmp_path / "dynamic.json"
        with open(dynamic_path, 'w') as f:
            json.dump([], f)

        # Should raise FileNotFoundError for missing static and random
        with pytest.raises(FileNotFoundError):
            generate_baseline_comparison(
                str(dynamic_path),
                str(tmp_path / "static.json"),
                str(tmp_path / "random.json"),
                str(output_path)
            )