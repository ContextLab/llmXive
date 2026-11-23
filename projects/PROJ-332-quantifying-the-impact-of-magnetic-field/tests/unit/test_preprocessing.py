"""
Unit tests for the preprocessing module.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

from code.data.preprocessing import (
    align_time_series,
    extract_snapshot,
    calculate_island_width,
    determine_confinement_mode,
    parse_discharge_data,
    process_multiple_discharges,
    validate_parsed_data
)


class TestAlignTimeSeries:
    def test_align_basic(self):
        """Test basic time alignment with two signals."""
        time_ref = np.linspace(0, 1, 100)
        time_sig = np.linspace(0, 1, 50)
        values_ref = np.ones(100)
        values_sig = np.ones(50) * 2

        signals = {
            'time': (time_ref, values_ref),
            'signal1': (time_sig, values_sig)
        }

        df = align_time_series(signals)

        assert 'time' in df.columns
        assert 'signal1' in df.columns
        assert len(df) == 100
        assert np.allclose(df['signal1'], 2.0)

    def test_align_missing_reference(self):
        """Test error handling when reference signal is missing."""
        signals = {
            'signal1': (np.linspace(0, 1, 50), np.ones(50))
        }

        with pytest.raises(ValueError, match="Reference signal 'time' not found"):
            align_time_series(signals)

    def test_align_mismatched_lengths(self):
        """Test alignment with signals of different lengths."""
        time_ref = np.linspace(0, 1, 100)
        time_sig = np.linspace(0, 0.5, 25)  # Different time range
        values_ref = np.ones(100)
        values_sig = np.ones(25) * 3

        signals = {
            'time': (time_ref, values_ref),
            'signal1': (time_sig, values_sig)
        }

        df = align_time_series(signals)
        assert len(df) == 100
        # Values should be interpolated
        assert not np.allclose(df['signal1'], 3.0)


class TestExtractSnapshot:
    def test_extract_window(self):
        """Test extraction within a time window."""
        time_arr = np.linspace(-0.2, 0.5, 100)
        values = np.arange(100)
        df = pd.DataFrame({'time': time_arr, 'value': values})

        snapshot = extract_snapshot(df, time_window=(-0.1, 0.1))

        assert len(snapshot) > 0
        assert (snapshot['time'] >= -0.1).all()
        assert (snapshot['time'] <= 0.1).all()

    def test_extract_target_time(self):
        """Test extraction at a specific time."""
        time_arr = np.linspace(0, 1, 100)
        values = np.arange(100)
        df = pd.DataFrame({'time': time_arr, 'value': values})

        snapshot = extract_snapshot(df, target_time=0.5)

        assert len(snapshot) == 1
        assert np.isclose(snapshot['time'].iloc[0], 0.5, atol=0.01)

    def test_extract_empty_window(self):
        """Test extraction when window contains no data."""
        time_arr = np.linspace(0, 1, 100)
        values = np.arange(100)
        df = pd.DataFrame({'time': time_arr, 'value': values})

        snapshot = extract_snapshot(df, time_window=(10, 20))

        assert snapshot.empty


class TestCalculateIslandWidth:
    def test_calculate_positive_shear(self):
        """Test island width calculation with positive shear."""
        df = pd.DataFrame()
        width = calculate_island_width(df, local_shear=0.5, q_value=3.0, magnetic_field=2.0, r_minor=0.6)

        assert width > 0
        assert isinstance(width, float)

    def test_calculate_zero_shear(self):
        """Test island width calculation with zero shear."""
        df = pd.DataFrame()
        width = calculate_island_width(df, local_shear=0.0, q_value=3.0, magnetic_field=2.0, r_minor=0.6)

        assert width == 0.0


class TestDetermineConfinementMode:
    def test_h_mode(self):
        """Test H-mode classification."""
        mode = determine_confinement_mode(h98y2=0.9)
        assert mode == 'H-mode'

    def test_l_mode(self):
        """Test L-mode classification."""
        mode = determine_confinement_mode(h98y2=0.7)
        assert mode == 'L-mode'

    def test_boundary(self):
        """Test classification at threshold."""
        mode = determine_confinement_mode(h98y2=0.85)
        assert mode == 'H-mode'


class TestValidateParsedData:
    def test_valid_data(self):
        """Test validation with valid data."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3],
            'tau_e': [1.0, 1.1, 0.9],
            'island_width': [0.01, 0.02, 0.015],
            'confinement_mode': ['L-mode', 'H-mode', 'L-mode']
        })

        is_valid, errors = validate_parsed_data(df)
        assert is_valid
        assert len(errors) == 0

    def test_missing_columns(self):
        """Test validation with missing columns."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3],
            'tau_e': [1.0, 1.1, 0.9]
        })

        is_valid, errors = validate_parsed_data(df)
        assert not is_valid
        assert any('Missing required columns' in e for e in errors)

    def test_invalid_modes(self):
        """Test validation with invalid confinement modes."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3],
            'tau_e': [1.0, 1.1, 0.9],
            'island_width': [0.01, 0.02, 0.015],
            'confinement_mode': ['L-mode', 'Unknown', 'L-mode']
        })

        is_valid, errors = validate_parsed_data(df)
        assert not is_valid
        assert any('Invalid confinement modes' in e for e in errors)

    def test_non_positive_tau_e(self):
        """Test validation with non-positive tau_e."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3],
            'tau_e': [1.0, 0.0, 0.9],
            'island_width': [0.01, 0.02, 0.015],
            'confinement_mode': ['L-mode', 'H-mode', 'L-mode']
        })

        is_valid, errors = validate_parsed_data(df)
        assert not is_valid
        assert any('tau_e contains non-positive values' in e for e in errors)
