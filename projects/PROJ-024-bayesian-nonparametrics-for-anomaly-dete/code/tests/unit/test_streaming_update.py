"""
Unit tests for streaming update logic in DPGMM model.

This test suite verifies that the streaming posterior update mechanism
works correctly, including:
- Single observation processing
- Batch observation processing
- ELBO convergence tracking
- Anomaly score computation in streaming mode
- Edge cases (missing values, empty batches)

Tests are designed to fail before implementation (TDD approach).
"""
import pytest
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.models.dpgmm import DPGMMModel, DPGMMConfig, compute_anomaly_score
from src.data.synthetic_generator import generate_synthetic_timeseries
from src.models.time_series import TimeSeries, TimeSeriesIterator
from src.utils.streaming import StreamingObservation


class TestStreamingObservation:
    """Tests for the StreamingObservation utility."""

    def test_create_streaming_observation(self):
        """Test creation of a single streaming observation."""
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=1.5,
            features={'source': 'test'}
        )
        assert obs.value == 1.5
        assert obs.source == 'test'

    def test_streaming_observation_with_missing_value(self):
        """Test streaming observation with missing value."""
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=np.nan,
            features={'source': 'test'}
        )
        assert obs.value is None or np.isnan(obs.value)


class TestDPGMMStreamingUpdate:
    """Tests for DPGMM streaming update logic."""

    @pytest.fixture
    def config(self):
        """Create a minimal DPGMM config for testing."""
        return DPGMMConfig(
            alpha_0=1.0,
            beta_0=1.0,
            kappa_0=1.0,
            nu_0=2,
            max_components=10,
            min_components=1,
            convergence_threshold=1e-4,
            max_iterations=100,
            random_seed=42
        )

    @pytest.fixture
    def model(self, config):
        """Create a fresh DPGMM model for testing."""
        return DPGMMModel(config=config)

    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic time series data for testing."""
        data = generate_synthetic_timeseries(
          n_points=100,
          n_anomalies=5,
          anomaly_rate=0.05,
          seed=42
        )
        return data

    def test_model_initialization(self, model):
        """Test that model initializes with correct state."""
        assert model is not None
        assert model.n_components == 0
        assert model.elbo_history == []

    def test_streaming_single_observation(self, model, config):
        """Test processing a single streaming observation."""
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            features={'batch': 0}
        )

        # Process single observation
        result = model.update(obs)

        assert result is not None
        assert result.observation_processed is True
        # After first observation, we should have at least one component
        assert model.n_components >= 1

    def test_streaming_batch_update(self, model, config, synthetic_data):
        """Test processing a batch of streaming observations."""
        # Create batch of observations
        values = synthetic_data['values'][:10]
        observations = [
            StreamingObservation(
                timestamp=datetime.now(),
                value=float(v),
                features={'batch': i}
            )
            for i, v in enumerate(values)
        ]

        # Process batch
        results = model.update_batch(observations)

        assert len(results) == len(observations)
        assert all(r.observation_processed for r in results)
        # Model should have learned some structure
        assert model.n_components >= 1

    def test_elbo_tracking_during_streaming(self, model, config, synthetic_data):
        """Test that ELBO is tracked during streaming updates."""
        # Process several observations
        values = synthetic_data['values'][:20]
        for v in values:
            obs = StreamingObservation(
                timestamp=datetime.now(),
                value=float(v),
                features={}
            )
            model.update(obs)

        # ELBO history should have entries
        assert len(model.elbo_history) > 0
        # ELBO values should be finite
        for elbo_entry in model.elbo_history:
            assert np.isfinite(elbo_entry.elbo_value)

    def test_anomaly_score_streaming(self, model, config, synthetic_data):
        """Test anomaly score computation in streaming mode."""
        # Process normal observations first
        normal_values = synthetic_data['values'][:50]
        for v in normal_values:
            obs = StreamingObservation(
                timestamp=datetime.now(),
                value=float(v),
                features={}
            )
            model.update(obs)

        # Test anomaly scoring on new observation
        anomalous_value = float(synthetic_data['values'][50])  # May be anomaly
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=anomalous_value,
            features={}
        )

        score = model.score_anomaly(obs)
        assert score is not None
        assert np.isfinite(score.score)

    def test_missing_value_handling(self, model, config):
        """Test handling of missing values in streaming mode."""
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=np.nan,
            features={'missing': True}
        )

        # Should handle missing value gracefully
        result = model.update(obs)
        # Result should indicate observation was processed (or skipped)
        assert result is not None

    def test_convergence_detection(self, model, config, synthetic_data):
        """Test that convergence is detected during streaming."""
        # Process many observations
        values = synthetic_data['values'][:100]
        for v in values:
            obs = StreamingObservation(
                timestamp=datetime.now(),
                value=float(v),
                features={}
            )
            model.update(obs)

        # Check that convergence was tracked
        if len(model.elbo_history) > 10:
            # Should have detected convergence at some point
            elbo_values = [e.elbo_value for e in model.elbo_history]
            # ELBO should generally increase (variational lower bound)
            assert len(set(elbo_values)) > 1  # Not constant

    def test_component_growth_limit(self, model, config):
        """Test that component count respects max_components."""
        # Process many diverse observations
        values = np.random.randn(200).tolist()
        for v in values:
            obs = StreamingObservation(
                timestamp=datetime.now(),
                value=float(v),
                features={}
            )
            model.update(obs)

        # Should not exceed max_components
        assert model.n_components <= config.max_components

    def test_empty_batch_handling(self, model, config):
        """Test handling of empty observation batch."""
        results = model.update_batch([])
        assert results == []
        # Model state should be unchanged
        assert model.n_components == 0

    def test_streaming_iterator_integration(self, model, config, synthetic_data):
        """Test integration with TimeSeriesIterator."""
        ts = TimeSeries(
            values=synthetic_data['values'],
            timestamps=[datetime.now()] * len(synthetic_data['values']),
            metadata={'source': 'test'}
        )
        iterator = TimeSeriesIterator(ts)

        # Process through iterator
        count = 0
        for obs in iterator:
            obs_with_ts = StreamingObservation(
                timestamp=obs.timestamp,
                value=obs.value,
                features={}
            )
            model.update(obs_with_ts)
            count += 1
            if count >= 10:  # Test partial iteration
                break

        assert count > 0
        assert model.n_components >= 1


class TestStreamingPerformance:
    """Performance-related tests for streaming updates."""

    def test_update_timing(self, config):
        """Test that single observation update completes quickly."""
        import time

        model = DPGMMModel(config=config)
        obs = StreamingObservation(
            timestamp=datetime.now(),
            value=1.0,
            features={}
        )

        start = time.time()
        model.update(obs)
        elapsed = time.time() - start

        # Should complete within reasonable time (<1s for single obs)
        assert elapsed < 1.0

    def test_batch_update_timing(self, config):
        """Test that batch update is efficient."""
        import time

        model = DPGMMModel(config=config)
        observations = [
            StreamingObservation(
                timestamp=datetime.now(),
                value=float(i),
                features={}
            )
            for i in range(50)
        ]

        start = time.time()
        results = model.update_batch(observations)
        elapsed = time.time() - start

        # Should complete within reasonable time (<5s for 50 obs)
        assert elapsed < 5.0
        assert len(results) == 50


class TestStreamingEdgeCases:
    """Edge case tests for streaming updates."""

    def test_extreme_values(self, config):
        """Test handling of extreme values."""
        model = DPGMMModel(config=config)

        # Very large value
        obs_large = StreamingObservation(
            timestamp=datetime.now(),
            value=1e10,
            features={}
        )
        result_large = model.update(obs_large)
        assert result_large is not None

        # Very small value
        obs_small = StreamingObservation(
            timestamp=datetime.now(),
            value=1e-10,
            features={}
        )
        result_small = model.update(obs_small)
        assert result_small is not None

    def test_repeated_values(self, config):
        """Test handling of repeated identical values."""
        model = DPGMMModel(config=config)

        # Many identical observations
        for _ in range(50):
            obs = StreamingObservation(
                timestamp=datetime.now(),
                value=1.0,
                features={}
            )
            model.update(obs)

        # Should handle without error
        assert model.n_components >= 1

    def test_timestamp_ordering(self, config):
        """Test handling of out-of-order timestamps."""
        model = DPGMMModel(config=config)

        # Out-of-order timestamps
        times = [
            datetime(2024, 1, 2),
            datetime(2024, 1, 1),
            datetime(2024, 1, 3),
        ]

        for t in times:
            obs = StreamingObservation(
                timestamp=t,
                value=1.0,
                features={}
            )
            model.update(obs)

        # Should handle without error
        assert model.n_components >= 1


def run_tests():
    """Run all streaming update tests."""
    pytest.main([__file__, '-v'])


if __name__ == '__main__':
    run_tests()
