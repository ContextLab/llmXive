import pytest
import pandas as pd
import numpy as np
from src.data.process import calculate_expected_probability, calculate_outcome_deviation, process_game_records

class TestCalculateExpectedProbability:
    def test_white_stronger(self):
        # White 1600, Black 1200 -> White should have high win prob
        prob = calculate_expected_probability(1600, 1200)
        assert 0.90 < prob < 0.99  # Expected ~0.94

    def test_equal_ratings(self):
        # Equal ratings -> 0.5
        prob = calculate_expected_probability(1500, 1500)
        assert abs(prob - 0.5) < 0.001

    def test_black_stronger(self):
        # White 1200, Black 1600 -> White should have low win prob
        prob = calculate_expected_probability(1200, 1600)
        assert 0.01 < prob < 0.10  # Expected ~0.05

    def test_nan_handling(self):
        assert np.isnan(calculate_expected_probability(np.nan, 1500))
        assert np.isnan(calculate_expected_probability(1500, np.nan))

class TestCalculateOutcomeDeviation:
    def test_white_win_expected(self):
        # White wins (1.0), expected 0.8 -> deviation 0.2
        dev = calculate_outcome_deviation(1.0, 0.8)
        assert dev == 0.2

    def test_black_win_expected(self):
        # Black wins (0.0), expected 0.8 -> deviation -0.8
        dev = calculate_outcome_deviation(0.0, 0.8)
        assert dev == -0.8

    def test_draw_expected(self):
        # Draw (0.5), expected 0.5 -> deviation 0.0
        dev = calculate_outcome_deviation(0.5, 0.5)
        assert dev == 0.0

    def test_nan_handling(self):
        assert np.isnan(calculate_outcome_deviation(np.nan, 0.5))
        assert np.isnan(calculate_outcome_deviation(0.5, np.nan))

class TestProcessGameRecords:
    def setup_method(self):
        self.valid_data = pd.DataFrame({
            'game_id': ['g1', 'g2', 'g3'],
            'white_rating': [1500, 1600, 1400],
            'black_rating': [1500, 1200, 1600],
            'outcome': [0.5, 1.0, 0.0]
        })

    def test_successful_processing(self):
        result = process_game_records(self.valid_data, validate=False)
        assert 'elo_expected_prob' in result.columns
        assert 'outcome_deviation' in result.columns
        assert len(result) == 3

    def test_malformed_skipped(self):
        data_with_errors = pd.DataFrame({
            'game_id': ['g1', 'g2', 'g3', 'g4'],
            'white_rating': [1500, 1600, np.nan, 1400], # g3 missing rating
            'black_rating': [1500, 1200, 1500, 1600],
            'outcome': [0.5, 1.0, 0.0, 0.9] # g4 invalid outcome
        })
        result = process_game_records(data_with_errors, validate=False)
        assert len(result) == 2
        assert result['game_id'].tolist() == ['g1', 'g2']

    def test_sc001_violation_raises_error(self):
        # Create a dataset where > 10% are malformed
        many_valid = pd.DataFrame({
            'game_id': [f'g{i}' for i in range(90)],
            'white_rating': [1500] * 90,
            'black_rating': [1500] * 90,
            'outcome': [0.5] * 90
        })
        many_malformed = pd.DataFrame({
            'game_id': [f'bad{i}' for i in range(20)],
            'white_rating': [np.nan] * 20,
            'black_rating': [1500] * 20,
            'outcome': [0.5] * 20
        })
        combined = pd.concat([many_valid, many_malformed], ignore_index=True)
        
        with pytest.raises(RuntimeError, match="SC-001 Violation"):
            process_game_records(combined, validate=True)

    def test_empty_input(self):
        empty_df = pd.DataFrame(columns=['game_id', 'white_rating', 'black_rating', 'outcome'])
        result = process_game_records(empty_df, validate=False)
        assert result.empty

    def test_all_malformed_raises_error(self):
        all_bad = pd.DataFrame({
            'game_id': ['g1'],
            'white_rating': [np.nan],
            'black_rating': [1500],
            'outcome': [0.5]
        })
        with pytest.raises(ValueError, match="No valid game records found"):
            process_game_records(all_bad, validate=False)