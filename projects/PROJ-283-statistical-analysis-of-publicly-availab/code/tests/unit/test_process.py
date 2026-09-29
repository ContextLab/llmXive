import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path
import sys

# Add code root to path
code_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(code_root))

from src.data.process import OnlineAccumulator, process_stream, save_inclusion_metrics, validate_inclusion_rate
from src.data.models import GameRecord

class TestOnlineAccumulator:
    def test_add_record_increments_counts(self):
        acc = OnlineAccumulator()
        record: GameRecord = {
            "game_id": "1", "white_rating": 1500.0, "black_rating": 1500.0,
            "eco_code": "C00", "avg_move_time_white": 10.0, "avg_move_time_black": 10.0,
            "material_imbalance_move10": 0.0, "material_imbalance_move5": 0.0,
            "outcome": 0.5, "elo_expected_prob": 0.5, "outcome_deviation": 0.0
        }
        acc.add_record(record)
        assert acc.total_games == 1
        assert acc.parsed_games == 1

    def test_add_none_increments_excluded(self):
        acc = OnlineAccumulator()
        acc.add_record(None)
        assert acc.total_games == 1
        assert acc.parsed_games == 0
        assert acc.excluded_games == 1

    def test_inclusion_rate_check_raises_on_low_rate(self):
        acc = OnlineAccumulator()
        # Force low rate: 1 total, 0 parsed -> rate 0.0
        acc.add_record(None)
        with pytest.raises(ValueError, match="Inclusion rate"):
            acc.add_record(None) # This might trigger the check depending on logic

    def test_finalize_returns_counts(self):
        acc = OnlineAccumulator()
        record: GameRecord = {
            "game_id": "1", "white_rating": 1500.0, "black_rating": 1500.0,
            "eco_code": "C00", "avg_move_time_white": 10.0, "avg_move_time_black": 10.0,
            "material_imbalance_move10": 0.0, "material_imbalance_move5": 0.0,
            "outcome": 0.5, "elo_expected_prob": 0.5, "outcome_deviation": 0.0
        }
        acc.add_record(record)
        counts = acc.finalize()
        assert "total_games" in counts
        assert "parsed_games" in counts
        assert "inclusion_rate" in counts

class TestProcessStream:
    def test_process_stream_writes_files(self, tmp_path):
        # Create a mock stream
        def mock_stream():
            for i in range(5):
                yield {
                    "game_id": f"game_{i}", "white_rating": 1500.0, "black_rating": 1500.0,
                    "eco_code": "C00", "avg_move_time_white": 10.0, "avg_move_time_black": 10.0,
                    "material_imbalance_move10": 0.0, "material_imbalance_move5": 0.0,
                    "outcome": 0.5, "elo_expected_prob": 0.5, "outcome_deviation": 0.0
                }
        
        parquet_path = tmp_path / "games.parquet"
        counts_path = tmp_path / "counts.json"
        
        counts = process_stream(mock_stream(), str(parquet_path), str(counts_path))
        
        assert parquet_path.exists()
        assert counts_path.exists()
        
        # Verify parquet content
        df = pd.read_parquet(parquet_path)
        assert len(df) == 5
        assert "game_id" in df.columns

    def test_process_stream_empty_stream(self, tmp_path):
        def empty_stream():
            return
            yield # Unreachable
        
        parquet_path = tmp_path / "empty.parquet"
        counts_path = tmp_path / "empty_counts.json"
        
        counts = process_stream(empty_stream(), str(parquet_path), str(counts_path))
        
        assert counts["total_games"] == 0
        assert counts["parsed_games"] == 0
        assert parquet_path.exists()

class TestInclusionMetrics:
    def test_save_inclusion_metrics_valid(self, tmp_path):
        counts = {"total_games": 100, "parsed_games": 95, "inclusion_rate": 0.95}
        path = tmp_path / "metrics.json"
        save_inclusion_metrics(counts, str(path))
        assert path.exists()
        with open(path) as f:
            data = json.load(f)
        assert data["inclusion_rate"] == 0.95

    def test_save_inclusion_metrics_invalid_rate_raises(self, tmp_path):
        counts = {"total_games": 100, "parsed_games": 90, "inclusion_rate": 0.90}
        path = tmp_path / "metrics.json"
        with pytest.raises(ValueError, match="Data quality gate failed"):
            save_inclusion_metrics(counts, str(path))