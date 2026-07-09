"""
Unit tests for code/features/labels.py
Specifically testing gaze variance calculation and min-max scaling.
"""
import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import MinMaxScaler

# Import the functions to be tested
from code.features.labels import compute_gaze_variance, generate_cognitive_load_labels, normalize_labels


class TestComputeGazeVariance:
    """Tests for compute_gaze_variance function."""

    def test_variance_calculation_basic(self):
        """Verify that variance is calculated correctly for a simple set."""
        # Create a simple DataFrame with gaze data
        data = {
            'x': [1.0, 2.0, 3.0, 4.0, 5.0],
            'y': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)

        # Calculate variance
        variance = compute_gaze_variance(df)

        # Expected variance for [1, 2, 3, 4, 5] is 2.0 (population variance)
        # or 2.5 (sample variance). Mne/pandas usually default to sample variance (ddof=1).
        # Let's check the sum of variances for x and y
        expected_x_var = df['x'].var()
        expected_y_var = df['y'].var()
        expected_total = expected_x_var + expected_y_var

        assert np.isclose(variance, expected_total), f"Expected {expected_total}, got {variance}"

    def test_variance_calculation_constant(self):
        """Verify variance is zero for constant data."""
        data = {
            'x': [5.0, 5.0, 5.0, 5.0],
            'y': [5.0, 5.0, 5.0, 5.0]
        }
        df = pd.DataFrame(data)

        variance = compute_gaze_variance(df)

        assert variance == 0.0, f"Expected 0.0 for constant data, got {variance}"

    def test_variance_calculation_empty(self):
        """Verify handling of empty DataFrame."""
        df = pd.DataFrame(columns=['x', 'y'])

        # Should return 0.0 or handle gracefully
        variance = compute_gaze_variance(df)
        assert variance == 0.0, f"Expected 0.0 for empty data, got {variance}"

    def test_variance_calculation_single_row(self):
        """Verify handling of single row (variance should be 0 or NaN handled)."""
        data = {
            'x': [1.0],
            'y': [2.0]
        }
        df = pd.DataFrame(data)

        variance = compute_gaze_variance(df)
        # Single point variance is typically 0.0 in this context or NaN handled to 0
        assert variance == 0.0, f"Expected 0.0 for single row, got {variance}"


class TestGenerateCognitiveLoadLabels:
    """Tests for generate_cognitive_load_labels function."""

    def test_label_generation_basic(self):
        """Verify labels are generated for a set of epochs."""
        # Simulate epoch metadata with gaze variance
        epochs_data = [
            {'epoch_id': 1, 'subject_id': 'S01', 'gaze_variance': 1.0},
            {'epoch_id': 2, 'subject_id': 'S01', 'gaze_variance': 2.0},
            {'epoch_id': 3, 'subject_id': 'S01', 'gaze_variance': 3.0},
        ]
        df_epochs = pd.DataFrame(epochs_data)

        # Generate labels
        df_labels = generate_cognitive_load_labels(df_epochs)

        assert 'cognitive_load' in df_labels.columns
        assert len(df_labels) == 3
        assert df_labels['subject_id'].iloc[0] == 'S01'

    def test_label_generation_multiple_subjects(self):
        """Verify labels are generated correctly for multiple subjects."""
        epochs_data = [
            {'epoch_id': 1, 'subject_id': 'S01', 'gaze_variance': 1.0},
            {'epoch_id': 2, 'subject_id': 'S01', 'gaze_variance': 2.0},
            {'epoch_id': 3, 'subject_id': 'S02', 'gaze_variance': 5.0},
            {'epoch_id': 4, 'subject_id': 'S02', 'gaze_variance': 10.0},
        ]
        df_epochs = pd.DataFrame(epochs_data)

        df_labels = generate_cognitive_load_labels(df_epochs)

        assert len(df_labels) == 4
        assert set(df_labels['subject_id'].unique()) == {'S01', 'S02'}


class TestNormalizeLabels:
    """Tests for normalize_labels function (min-max scaling)."""

    def test_min_max_scaling_basic(self):
        """Verify min-max scaling maps values to [0, 1]."""
        # Create a DataFrame with cognitive load scores
        data = {
            'subject_id': ['S01', 'S01', 'S01', 'S01'],
            'cognitive_load': [10.0, 20.0, 30.0, 40.0]
        }
        df = pd.DataFrame(data)

        # Normalize
        df_normalized = normalize_labels(df)

        # Check that min is 0 and max is 1 for S01
        s01_data = df_normalized[df_normalized['subject_id'] == 'S01']['cognitive_load']
        assert np.isclose(s01_data.min(), 0.0), f"Min should be 0.0, got {s01_data.min()}"
        assert np.isclose(s01_data.max(), 1.0), f"Max should be 1.0, got {s01_data.max()}"

    def test_min_max_scaling_constant(self):
        """Verify handling of constant values (all same)."""
        data = {
            'subject_id': ['S01', 'S01', 'S01'],
            'cognitive_load': [5.0, 5.0, 5.0]
        }
        df = pd.DataFrame(data)

        df_normalized = normalize_labels(df)

        # When min == max, the result is typically 0.0 or handled specifically
        # Based on sklearn MinMaxScaler, it returns 0.0 for constant inputs
        s01_data = df_normalized[df_normalized['subject_id'] == 'S01']['cognitive_load']
        assert all(s01_data == 0.0), f"Expected all 0.0 for constant input, got {s01_data.tolist()}"

    def test_min_max_scaling_multiple_subjects(self):
        """Verify min-max scaling is applied per subject."""
        data = {
            'subject_id': ['S01', 'S01', 'S02', 'S02'],
            'cognitive_load': [10.0, 20.0, 100.0, 200.0]
        }
        df = pd.DataFrame(data)

        df_normalized = normalize_labels(df)

        # Check S01
        s01_data = df_normalized[df_normalized['subject_id'] == 'S01']['cognitive_load']
        assert np.isclose(s01_data.min(), 0.0)
        assert np.isclose(s01_data.max(), 1.0)

        # Check S02
        s02_data = df_normalized[df_normalized['subject_id'] == 'S02']['cognitive_load']
        assert np.isclose(s02_data.min(), 0.0)
        assert np.isclose(s02_data.max(), 1.0)

    def test_min_max_scaling_range(self):
        """Verify output is strictly within [0, 1]."""
        data = {
            'subject_id': ['S01'] * 10,
            'cognitive_load': np.random.rand(10) * 100
        }
        df = pd.DataFrame(data)

        df_normalized = normalize_labels(df)
        values = df_normalized['cognitive_load']

        assert values.min() >= 0.0, "Min value should be >= 0"
        assert values.max() <= 1.0, "Max value should be <= 1"