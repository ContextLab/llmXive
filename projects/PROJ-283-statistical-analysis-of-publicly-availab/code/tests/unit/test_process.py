import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.data.process import OnlineAccumulator, calculate_expected_probability, calculate_outcome_deviation, process_stream

class TestOnlineAccumulator:
    def test_init(self, tmp_path):
        output_path = tmp_path / "test.parquet"
        counts_path = tmp_path / "counts.json"
        acc = OnlineAccumulator(str(output_path), str(counts_path))
        assert acc.total_games == 0
        assert acc.parsed_games == 0
        assert acc.output_path == output_path
        assert acc.counts_output_path == counts_path

    def test_add_record_valid(self, tmp_path):
        output_path = tmp_path / "test.parquet"
        counts_path = tmp_path / "counts.json"
        acc = OnlineAccumulator(str(output_path), str(counts_path))
        
        record = {
            'game_id': 'test1',
            'white_rating': 1500.0,
            'black_rating': 1500.0,
            'eco_code': 'B00',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0,
            'outcome': 1.0
        }
        
        acc.add_record(record)
        assert acc.total_games == 1
        assert acc.parsed_games == 1
        assert acc.excluded_games == 0

    def test_add_record_missing_ratings(self, tmp_path):
        output_path = tmp_path / "test.parquet"
        counts_path = tmp_path / "counts.json"
        acc = OnlineAccumulator(str(output_path), str(counts_path))
        
        record = {
            'game_id': 'test2',
            'white_rating': None,
            'black_rating': 1500.0,
            'eco_code': 'B00',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0,
            'outcome': 1.0
        }
        
        acc.add_record(record)
        assert acc.total_games == 1
        assert acc.parsed_games == 0
        assert acc.excluded_games == 1

    def test_finalize_writes_files(self, tmp_path):
        output_path = tmp_path / "test.parquet"
        counts_path = tmp_path / "counts.json"
        acc = OnlineAccumulator(str(output_path), str(counts_path))
        
        record = {
            'game_id': 'test3',
            'white_rating': 1500.0,
            'black_rating': 1500.0,
            'eco_code': 'B00',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0,
            'outcome': 1.0
        }
        acc.add_record(record)
        
        result = acc.finalize()
        
        assert output_path.exists()
        assert counts_path.exists()
        assert result['total_games'] == 1
        assert result['parsed_games'] == 1

        # Check counts content
        with open(counts_path, 'r') as f:
            data = json.load(f)
        assert data['total_games'] == 1
        assert data['parsed_games'] == 1

class TestProcessStream:
    def test_process_stream(self, tmp_path):
        output_path = tmp_path / "stream_test.parquet"
        counts_path = tmp_path / "stream_counts.json"
        
        def mock_iterator():
            for i in range(5):
                yield {
                    'game_id': f'game_{i}',
                    'white_rating': 1500.0 + i,
                    'black_rating': 1500.0 - i,
                    'eco_code': 'B00',
                    'avg_move_time_white': 10.0,
                    'avg_move_time_black': 10.0,
                    'material_imbalance_move10': 0.0,
                    'material_imbalance_move5': 0.0,
                    'outcome': 1.0 if i % 2 == 0 else 0.0
                }
        
        result = process_stream(mock_iterator(), str(output_path), str(counts_path))
        
        assert result['total_games'] == 5
        assert result['parsed_games'] == 5
        assert output_path.exists()
        assert counts_path.exists()

class TestCalculations:
    def test_calculate_expected_probability(self):
        # Equal ratings
        prob = calculate_expected_probability(1500, 1500)
        assert 0.49 <= prob <= 0.51
        
        # White much higher
        prob = calculate_expected_probability(2000, 1000)
        assert prob >= 0.99
        
        # Black much higher
        prob = calculate_expected_probability(1000, 2000)
        assert prob <= 0.01

    def test_calculate_outcome_deviation(self):
        dev = calculate_outcome_deviation(1.0, 0.5)
        assert dev == 0.5
        
        dev = calculate_outcome_deviation(0.0, 0.5)
        assert dev == -0.5