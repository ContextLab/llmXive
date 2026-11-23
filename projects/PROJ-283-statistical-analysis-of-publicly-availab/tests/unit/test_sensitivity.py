import pytest
import pandas as pd
import numpy as np
from src.reports.sensitivity import (
    calculate_jaccard_index,
    get_significant_predictors,
    perform_threshold_sweep
)


class TestJaccardIndex:
    def test_identical_sets(self):
        set_a = {1, 2, 3}
        set_b = {1, 2, 3}
        assert calculate_jaccard_index(set_a, set_b) == 1.0

    def test_disjoint_sets(self):
        set_a = {1, 2}
        set_b = {3, 4}
        assert calculate_jaccard_index(set_a, set_b) == 0.0

    def test_partial_overlap(self):
        set_a = {1, 2, 3}
        set_b = {2, 3, 4}
        # Intersection: {2, 3} (size 2)
        # Union: {1, 2, 3, 4} (size 4)
        assert calculate_jaccard_index(set_a, set_b) == 0.5

    def test_empty_sets(self):
        assert calculate_jaccard_index(set(), set()) == 0.0


class TestSignificantPredictors:
    def test_basic_filtering(self):
        df = pd.DataFrame({
            'predictor': ['p1', 'p2', 'p3'],
            'p_value': [0.01, 0.05, 0.20]
        })
        result = get_significant_predictors(df, 0.05)
        assert result == {'p1'}

    def test_boundary_case(self):
        df = pd.DataFrame({
            'predictor': ['p1', 'p2'],
            'p_value': [0.05, 0.06]
        })
        # Strictly less than or equal? Usually <= 0.05 is significant
        # Assuming <= based on standard practice
        result = get_significant_predictors(df, 0.05)
        assert 'p1' in result
        assert 'p2' not in result

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['predictor', 'p_value'])
        result = get_significant_predictors(df, 0.05)
        assert result == set()


class TestThresholdSweep:
    def test_sweep_logic(self):
        # Create a mock DataFrame with known p-values
        data = {
            'predictor': ['A', 'B', 'C', 'D'],
            'p_value': [0.01, 0.04, 0.06, 0.09]
        }
        df = pd.DataFrame(data)

        thresholds = [0.05, 0.10]
        results = perform_threshold_sweep(df, thresholds)

        # Check that results are returned
        assert len(results) == len(thresholds)

        # Verify specific outcomes
        # For 0.05: A, B should be significant
        # For 0.10: A, B, C should be significant (D is 0.09? No, D is 0.09 which is < 0.10)
        # Wait, D is 0.09. 0.09 < 0.10. So A, B, C, D?
        # Let's recheck values: 0.01, 0.04, 0.06, 0.09
        # Thresh 0.05: 0.01, 0.04 -> {A, B}
        # Thresh 0.10: 0.01, 0.04, 0.06, 0.09 -> {A, B, C, D}

        assert results[0]['threshold'] == 0.05
        assert results[0]['significant_predictors'] == {'A', 'B'}

        assert results[1]['threshold'] == 0.10
        assert results[1]['significant_predictors'] == {'A', 'B', 'C', 'D'}

    def test_no_significant_predictors(self):
        df = pd.DataFrame({
            'predictor': ['X'],
            'p_value': [0.99]
        })
        results = perform_threshold_sweep(df, [0.05])
        assert results[0]['significant_predictors'] == set()