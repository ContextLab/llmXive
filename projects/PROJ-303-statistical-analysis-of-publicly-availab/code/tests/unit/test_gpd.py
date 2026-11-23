"""
Unit tests for the GPD Baseline Model.

Tests:
    - Verify independent GPD parameters are station-specific.
    - Verify fit fails gracefully with insufficient data.
    - Verify probability and intensity predictions are consistent.
"""

import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import json

from src.models.gpd_baseline import GPDBaseline, fit_gpd_baseline


class TestGPDBaseline:
    """Tests for the GPDBaseline class."""

    def create_mock_exceedances(self, n_stations=3, n_events=50):
        """Create a mock DataFrame of extreme events for testing."""
        data = []
        for i in range(n_stations):
            station_id = f"STN_{i:03d}"
            # Generate random exceedances (positive values)
            magnitudes = np.random.exponential(scale=2.0, size=n_events)
            thresholds = np.random.uniform(10.0, 20.0, size=n_events)
            for mag, thr in zip(magnitudes, thresholds):
                data.append({
                    'station_id': station_id,
                    'magnitude': mag,
                    'threshold_value': thr
                })
        return pd.DataFrame(data)

    def test_fit_success(self):
        """Test that the model fits successfully on valid data."""
        df = self.create_mock_exceedances()
        model = GPDBaseline()
        model.fit(df)

        assert model._fitted is True
        assert len(model.parameters) > 0
        assert all(s in model.fit_status for s in model.station_ids)
        assert model.fit_status[list(model.parameters.keys())[0]] == 'success'

    def test_station_specific_parameters(self):
        """Verify that parameters are different for each station."""
        df = self.create_mock_exceedances(n_stations=3, n_events=100)
        model = GPDBaseline()
        model.fit(df)

        params = list(model.parameters.values())
        # Check that at least two stations have different parameters
        # (With random data, it's highly unlikely they are identical)
        shapes = [p['shape'] for p in params]
        scales = [p['scale'] for p in params]

        # Assert not all shapes are the same (within float precision)
        assert len(set(np.round(shapes, 5))) > 1 or len(set(np.round(scales, 5))) > 1

    def test_insufficient_data_handling(self):
        """Test that stations with too few events are handled gracefully."""
        # Create data where one station has very few events
        df = self.create_mock_exceedances(n_stations=2, n_events=50)
        # Add a third station with only 5 events
        low_data = pd.DataFrame([
            {'station_id': 'STN_LOW', 'magnitude': 1.0, 'threshold_value': 10.0}
            for _ in range(5)
        ])
        df = pd.concat([df, low_data], ignore_index=True)

        model = GPDBaseline()
        model.fit(df)

        assert 'STN_LOW' in model.fit_status
        assert model.fit_status['STN_LOW'] == 'insufficient_data'
        assert 'STN_LOW' not in model.parameters

    def test_predict_probability_consistency(self):
        """Test that predict_probability returns valid probabilities."""
        df = self.create_mock_exceedances()
        model = GPDBaseline()
        model.fit(df)

        station_id = list(model.parameters.keys())[0]
        params = model.parameters[station_id]

        # Test with a value above threshold
        threshold = 15.0
        value = 20.0
        prob = model.predict_probability(station_id, threshold, value)

        assert 0.0 <= prob <= 1.0

        # Test with value below threshold
        prob_below = model.predict_probability(station_id, threshold, 10.0)
        assert prob_below == 1.0

    def test_predict_intensity_monotonicity(self):
        """Test that higher probabilities correspond to lower intensities."""
        df = self.create_mock_exceedances()
        model = GPDBaseline()
        model.fit(df)

        station_id = list(model.parameters.keys())[0]
        threshold = 15.0

        p1 = 0.1  # Low probability -> High intensity
        p2 = 0.9  # High probability -> Low intensity

        val1 = model.predict_intensity(station_id, p1, threshold)
        val2 = model.predict_intensity(station_id, p2, threshold)

        assert val1 > val2

    def test_fit_missing_columns(self):
        """Test that fit raises ValueError for missing columns."""
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        model = GPDBaseline()

        with pytest.raises(ValueError):
            model.fit(df)

    def test_predict_unfitted_model(self):
        """Test that prediction fails if model is not fitted."""
        model = GPDBaseline()
        with pytest.raises(RuntimeError):
            model.predict_probability("STN_001", 10.0, 15.0)

    def test_predict_unknown_station(self):
        """Test that prediction fails for an unknown station."""
        df = self.create_mock_exceedances()
        model = GPDBaseline()
        model.fit(df)

        with pytest.raises(ValueError):
            model.predict_probability("UNKNOWN_STN", 10.0, 15.0)


class TestFitGpdBaselineFunction:
    """Tests for the fit_gpd_baseline main function."""

    def test_fit_and_save(self):
        """Test the full pipeline of fitting and saving parameters."""
        df = self.create_mock_exceedances()

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "events.parquet"
            output_path = Path(tmpdir) / "params.json"

            df.to_parquet(input_path)

            summary = fit_gpd_baseline(str(input_path), str(output_path))

            assert output_path.exists()
            assert summary['fitted_stations'] > 0

            with open(output_path, 'r') as f:
                data = json.load(f)
            assert 'model_type' in data
            assert 'fitted_stations' in data
            assert 'fit_status' in data

    def create_mock_exceedances(self, n_stations=3, n_events=50):
        """Helper to create mock data."""
        data = []
        for i in range(n_stations):
            station_id = f"STN_{i:03d}"
            magnitudes = np.random.exponential(scale=2.0, size=n_events)
            thresholds = np.random.uniform(10.0, 20.0, size=n_events)
            for mag, thr in zip(magnitudes, thresholds):
                data.append({
                    'station_id': station_id,
                    'magnitude': mag,
                    'threshold_value': thr
                })
        return pd.DataFrame(data)
