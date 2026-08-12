"""
Unit tests for the OnlineAccumulator and process_stream functions.
"""

import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.process import (
    OnlineAccumulator,
    process_stream,
    calculate_expected_probability,
    calculate_outcome_deviation,
    process_game_record,
    calculate_and_save_inclusion_metrics,
    validate_inclusion_rate
)


class TestCalculateExpectedProbability:
    """Tests for Elo probability calculation."""

    def test_equal_ratings(self):
        """Test probability when ratings are equal."""
        prob = calculate_expected_probability(1500, 1500)
        assert prob == pytest.approx(0.5, abs=0.001)

    def test_rating_difference(self):
        """Test probability with rating difference."""
        # White has 200 point advantage
        prob = calculate_expected_probability(1700, 1500)
        assert prob > 0.5

        # Black has 200 point advantage
        prob = calculate_expected_probability(1500, 1700)
        assert prob < 0.5

    def test_extreme_ratings_capped(self):
        """Test that extreme probabilities are capped."""
        # Very large rating difference
        prob = calculate_expected_probability(2800, 1000)
        assert prob <= 0.99

        prob = calculate_expected_probability(1000, 2800)
        assert prob >= 0.01


class TestCalculateOutcomeDeviation:
    """Tests for outcome deviation calculation."""

    def test_white_win(self):
        """Test deviation when white wins."""
        deviation = calculate_outcome_deviation(1.0, 0.6)
        assert deviation == 0.4

    def test_black_win(self):
        """Test deviation when black wins."""
        deviation = calculate_outcome_deviation(0.0, 0.4)
        assert deviation == -0.4

    def test_draw(self):
        """Test deviation for draw."""
        deviation = calculate_outcome_deviation(0.5, 0.5)
        assert deviation == 0.0


class TestProcessGameRecord:
    """Tests for game record processing."""

    def test_valid_game(self):
        """Test processing a valid game record."""
        game_data = {
            'game_id': 'test_001',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'B12',
            'outcome': '1-0',
            'avg_move_time_white': 10.5,
            'avg_move_time_black': 12.3,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0
        }

        result = process_game_record(game_data)

        assert result is not None
        assert result['game_id'] == 'test_001'
        assert result['outcome'] == 1.0
        assert 'elo_expected_prob' in result
        assert 'outcome_deviation' in result

    def test_missing_move_time(self):
        """Test that games with missing move times are excluded."""
        game_data = {
            'game_id': 'test_002',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'B12',
            'outcome': '1-0',
            'avg_move_time_white': 0.0,  # Missing
            'avg_move_time_black': 12.3,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0
        }

        result = process_game_record(game_data)
        assert result is None

    def test_invalid_ratings(self):
        """Test that games with invalid ratings are excluded."""
        game_data = {
            'game_id': 'test_003',
            'white_rating': 0,  # Invalid
            'black_rating': 1500,
            'eco_code': 'B12',
            'outcome': '1-0',
            'avg_move_time_white': 10.5,
            'avg_move_time_black': 12.3,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0
        }

        result = process_game_record(game_data)
        assert result is None


class TestOnlineAccumulator:
    """Tests for OnlineAccumulator class."""

    def test_initialization(self):
        """Test accumulator initialization."""
        acc = OnlineAccumulator()
        assert acc.total_games == 0
        assert acc.parsed_games == 0
        assert acc.min_inclusion_rate == 0.95

    def test_add_valid_game(self):
        """Test adding a valid game."""
        acc = OnlineAccumulator()
        game_data = {
            'game_id': 'test_001',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'B12',
            'outcome': '1-0',
            'avg_move_time_white': 10.5,
            'avg_move_time_black': 12.3,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0
        }

        result = acc.add_game(game_data)
        assert result is True
        assert acc.total_games == 1
        assert acc.parsed_games == 1

    def test_add_invalid_game(self):
        """Test adding an invalid game (excluded)."""
        acc = OnlineAccumulator()
        game_data = {
            'game_id': 'test_001',
            'white_rating': 0,  # Invalid
            'black_rating': 1500,
            'eco_code': 'B12',
            'outcome': '1-0',
            'avg_move_time_white': 10.5,
            'avg_move_time_black': 12.3,
            'material_imbalance_move10': 0.0,
            'material_imbalance_move5': 0.0
        }

        result = acc.add_game(game_data)
        assert result is False
        assert acc.total_games == 1
        assert acc.parsed_games == 0
        assert acc.excluded_games == 1

    def test_inclusion_rate_check(self):
        """Test that low inclusion rate raises error."""
        acc = OnlineAccumulator(min_inclusion_rate=0.5)

        # Add 10 valid games
        for i in range(10):
            game_data = {
                'game_id': f'test_{i:03d}',
                'white_rating': 1500,
                'black_rating': 1500,
                'eco_code': 'B12',
                'outcome': '1-0',
                'avg_move_time_white': 10.5,
                'avg_move_time_black': 12.3,
                'material_imbalance_move10': 0.0,
                'material_imbalance_move5': 0.0
            }
            acc.add_game(game_data)

        # Add many invalid games to drop rate below threshold
        for i in range(10, 200):
            game_data = {
                'game_id': f'test_{i:03d}',
                'white_rating': 0,  # Invalid
                'black_rating': 1500,
                'eco_code': 'B12',
                'outcome': '1-0',
                'avg_move_time_white': 10.5,
                'avg_move_time_black': 12.3,
                'material_imbalance_move10': 0.0,
                'material_imbalance_move5': 0.0
            }

            # This should raise ValueError when rate drops below 0.5
            if acc.total_games > 20:
                with pytest.raises(ValueError):
                    acc.add_game(game_data)
                break
            else:
                acc.add_game(game_data)

    def test_finalize_dataframe(self):
        """Test finalizing to DataFrame."""
        acc = OnlineAccumulator()

        # Add some valid games
        for i in range(5):
            game_data = {
                'game_id': f'test_{i:03d}',
                'white_rating': 1500 + i * 10,
                'black_rating': 1500 - i * 10,
                'eco_code': 'B12',
                'outcome': '1-0' if i % 2 == 0 else '0-1',
                'avg_move_time_white': 10.5 + i,
                'avg_move_time_black': 12.3 + i,
                'material_imbalance_move10': 0.0,
                'material_imbalance_move5': 0.0
            }
            acc.add_game(game_data)

        df = acc.finalize()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert 'game_id' in df.columns
        assert 'outcome_deviation' in df.columns

    def test_save_counts(self):
        """Test saving counts to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'counts.json')
            acc = OnlineAccumulator()

            # Add a game
            game_data = {
                'game_id': 'test_001',
                'white_rating': 1500,
                'black_rating': 1500,
                'eco_code': 'B12',
                'outcome': '1-0',
                'avg_move_time_white': 10.5,
                'avg_move_time_black': 12.3,
                'material_imbalance_move10': 0.0,
                'material_imbalance_move5': 0.0
            }
            acc.add_game(game_data)

            acc.save_counts(output_path)

            # Verify file exists and contains correct data
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['total_games'] == 1
            assert data['parsed_games'] == 1


class TestProcessStream:
    """Tests for process_stream function."""

    def test_process_stream_basic(self):
        """Test basic stream processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'games.parquet')
            counts_path = os.path.join(tmpdir, 'counts.json')

            # Create a simple generator
            def game_generator():
                for i in range(10):
                    yield {
                        'game_id': f'test_{i:03d}',
                        'white_rating': 1500 + i * 10,
                        'black_rating': 1500 - i * 10,
                        'eco_code': 'B12',
                        'outcome': '1-0' if i % 2 == 0 else '0-1',
                        'avg_move_time_white': 10.5 + i,
                        'avg_move_time_black': 12.3 + i,
                        'material_imbalance_move10': 0.0,
                        'material_imbalance_move5': 0.0
                    }

            metrics = process_stream(game_generator(), output_path, counts_path)

            assert metrics['total_games'] == 10
            assert metrics['parsed_games'] == 10
            assert os.path.exists(output_path)
            assert os.path.exists(counts_path)

            # Verify parquet file can be loaded
            df = pd.read_parquet(output_path)
            assert len(df) == 10
            assert 'outcome_deviation' in df.columns

            # Verify counts file
            with open(counts_path, 'r') as f:
                counts = json.load(f)
            assert counts['total_games'] == 10
            assert counts['parsed_games'] == 10

    def test_process_stream_with_exclusions(self):
        """Test stream processing with some excluded games."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'games.parquet')
            counts_path = os.path.join(tmpdir, 'counts.json')

            def game_generator():
                for i in range(20):
                    if i % 2 == 0:
                        # Valid game
                        yield {
                            'game_id': f'test_{i:03d}',
                            'white_rating': 1500,
                            'black_rating': 1500,
                            'eco_code': 'B12',
                            'outcome': '1-0',
                            'avg_move_time_white': 10.5,
                            'avg_move_time_black': 12.3,
                            'material_imbalance_move10': 0.0,
                            'material_imbalance_move5': 0.0
                        }
                    else:
                        # Invalid game (missing move time)
                        yield {
                            'game_id': f'test_{i:03d}',
                            'white_rating': 1500,
                            'black_rating': 1500,
                            'eco_code': 'B12',
                            'outcome': '1-0',
                            'avg_move_time_white': 0.0,  # Missing
                            'avg_move_time_black': 12.3,
                            'material_imbalance_move10': 0.0,
                            'material_imbalance_move5': 0.0
                        }

            metrics = process_stream(game_generator(), output_path, counts_path)

            assert metrics['total_games'] == 20
            assert metrics['parsed_games'] == 10  # Half excluded


class TestInclusionMetrics:
    """Tests for inclusion metrics functions."""

    def test_calculate_and_save_inclusion_metrics(self):
        """Test calculating and saving inclusion metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'metrics.json')

            rate = calculate_and_save_inclusion_metrics(
                total_games=100,
                parsed_games=95,
                output_path=output_path
            )

            assert rate == 0.95
            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                data = json.load(f)
            assert data['inclusion_rate'] == 0.95

    def test_validate_inclusion_rate(self):
        """Test inclusion rate validation."""
        assert validate_inclusion_rate(100, 95, 0.95) is True
        assert validate_inclusion_rate(100, 94, 0.95) is False
        assert validate_inclusion_rate(100, 100, 0.95) is True
        assert validate_inclusion_rate(0, 0, 0.95) is False

    def test_low_inclusion_rate_raises_error(self):
        """Test that low inclusion rate raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'metrics.json')

            with pytest.raises(ValueError):
                calculate_and_save_inclusion_metrics(
                    total_games=100,
                    parsed_games=80,  # Below 0.95 threshold
                    output_path=output_path
                )