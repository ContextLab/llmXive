import pytest
import pandas as pd
import numpy as np
from src.data.process import cap_probability, calculate_expected_probability, calculate_outcome_deviation, map_outcome_to_result, process_game_record

class TestProcessEdgeCases:
    """Additional unit tests for data processing edge cases."""

    def test_cap_probability_boundary_values(self):
        """Test probability capping at boundary values."""
        # Values within range
        assert cap_probability(0.5) == 0.5
        assert cap_probability(0.01) == 0.01
        assert cap_probability(0.99) == 0.99
        
        # Values outside range
        assert cap_probability(0.0) == 0.01
        assert cap_probability(1.0) == 0.99
        assert cap_probability(-0.5) == 0.01
        assert cap_probability(1.5) == 0.99

    def test_cap_probability_numerical_stability(self):
        """Test probability capping for numerical stability with extreme ratings."""
        # Extreme rating difference
        prob = calculate_expected_probability(1000, 3000)
        # This should be very close to 0, but capped at 0.01
        assert prob >= 0.01
        assert prob <= 0.99

    def test_calculate_expected_probability_equal_ratings(self):
        """Test expected probability with equal ratings."""
        prob = calculate_expected_probability(1500, 1500)
        assert abs(prob - 0.5) < 0.01

    def test_calculate_expected_probability_large_rating_difference(self):
        """Test expected probability with large rating difference."""
        # White 2000, Black 1000 -> White should have high probability
        prob = calculate_expected_probability(2000, 1000)
        assert prob > 0.9
        
        # Reverse
        prob_rev = calculate_expected_probability(1000, 2000)
        assert prob_rev < 0.1
        assert abs(prob + prob_rev - 1.0) < 0.01  # Should sum to ~1

    def test_calculate_outcome_deviation(self):
        """Test outcome deviation calculation."""
        # White wins (1.0) with expected 0.5
        assert calculate_outcome_deviation(1.0, 0.5) == 0.5
        
        # Black wins (0.0) with expected 0.5
        assert calculate_outcome_deviation(0.0, 0.5) == -0.5
        
        # Draw (0.5) with expected 0.5
        assert calculate_outcome_deviation(0.5, 0.5) == 0.0

    def test_map_outcome_to_result(self):
        """Test mapping of game outcomes to numerical results."""
        assert map_outcome_to_result("1-0") == 1.0
        assert map_outcome_to_result("0-1") == 0.0
        assert map_outcome_to_result("1/2-1/2") == 0.5
        assert map_outcome_to_result("*") == 0.5  # Draw or unknown

    def test_process_game_record_with_missing_data(self):
        """Test processing a game record with some missing data."""
        record = {
            'game_id': 'game1',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': None,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': '1-0'
        }
        
        # Should handle missing avg_move_time_white gracefully
        processed = process_game_record(record)
        assert processed is not None
        assert processed['game_id'] == 'game1'
        assert processed['elo_expected_prob'] is not None
        assert processed['outcome_deviation'] is not None

    def test_process_game_record_with_invalid_rating(self):
        """Test processing a game record with invalid rating."""
        record = {
            'game_id': 'game1',
            'white_rating': -100,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': '1-0'
        }
        
        # Should still process, but the probability might be extreme
        processed = process_game_record(record)
        assert processed is not None
        assert processed['elo_expected_prob'] is not None

    def test_process_game_record_with_zero_rating(self):
        """Test processing a game record with zero rating."""
        record = {
            'game_id': 'game1',
            'white_rating': 0,
            'black_rating': 0,
            'eco_code': 'C20',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': '1-0'
        }
        
        processed = process_game_record(record)
        assert processed is not None
        # With equal ratings (even if 0), probability should be 0.5
        assert abs(processed['elo_expected_prob'] - 0.5) < 0.01

    def test_process_game_record_with_missing_outcome(self):
        """Test processing a game record with missing outcome."""
        record = {
            'game_id': 'game1',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': None
        }
        
        # Should handle missing outcome gracefully
        processed = process_game_record(record)
        assert processed is not None
        # The outcome_deviation might be 0 or handled specially

    def test_process_game_record_with_string_ratings(self):
        """Test processing a game record with string ratings."""
        record = {
            'game_id': 'game1',
            'white_rating': '1500',
            'black_rating': '1500',
            'eco_code': 'C20',
            'avg_move_time_white': '10.0',
            'avg_move_time_black': '10.0',
            'material_imbalance_move5': '0.0',
            'outcome': '1-0'
        }
        
        # Should convert strings to floats
        processed = process_game_record(record)
        assert processed is not None
        assert isinstance(processed['elo_expected_prob'], float)

    def test_process_game_record_with_extreme_values(self):
        """Test processing a game record with extreme values."""
        record = {
            'game_id': 'game1',
            'white_rating': 3000,
            'black_rating': 1000,
            'eco_code': 'C20',
            'avg_move_time_white': 1000.0,
            'avg_move_time_black': 0.001,
            'material_imbalance_move5': 10.0,
            'outcome': '1-0'
        }
        
        processed = process_game_record(record)
        assert processed is not None
        assert processed['elo_expected_prob'] >= 0.01
        assert processed['elo_expected_prob'] <= 0.99

    def test_process_game_record_with_nan_values(self):
        """Test processing a game record with NaN values."""
        record = {
            'game_id': 'game1',
            'white_rating': np.nan,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': np.nan,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': np.nan,
            'outcome': '1-0'
        }
        
        # Should handle NaN gracefully
        processed = process_game_record(record)
        assert processed is not None
        # The elo_expected_prob might be NaN or handled specially

    def test_process_game_record_with_inf_values(self):
        """Test processing a game record with infinity values."""
        record = {
            'game_id': 'game1',
            'white_rating': np.inf,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': '1-0'
        }
        
        # Should handle infinity gracefully
        processed = process_game_record(record)
        assert processed is not None
        # The probability should be capped

    def test_process_game_record_with_empty_string_outcome(self):
        """Test processing a game record with empty string outcome."""
        record = {
            'game_id': 'game1',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': ''
        }
        
        processed = process_game_record(record)
        assert processed is not None
        # Empty string should be treated as unknown/draw

    def test_process_game_record_with_case_insensitive_outcome(self):
        """Test processing a game record with case-insensitive outcome."""
        record = {
            'game_id': 'game1',
            'white_rating': 1500,
            'black_rating': 1500,
            'eco_code': 'C20',
            'avg_move_time_white': 10.0,
            'avg_move_time_black': 10.0,
            'material_imbalance_move5': 0.0,
            'outcome': '1-0'
        }
        
        processed = process_game_record(record)
        assert processed is not None
        assert processed['outcome_deviation'] is not None
