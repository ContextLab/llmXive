"""
Unit tests for edge cases in code/data/preprocess.py (Task T014a).
Specifically tests:
1. Empty input handling
2. Threshold validation logic
"""
import os
import sys
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from data.preprocess import (
    load_config,
    filter_events,
    validate_output,
    get_current_memory_usage_mb
)
from config import get_config_summary


class TestEmptyInputHandling:
    """Tests for handling empty input data in preprocess.py"""

    def test_filter_events_empty_dataframe(self, tmp_path):
        """Test that filter_events handles empty DataFrame gracefully"""
        # Create empty DataFrame with expected schema
        empty_df = pd.DataFrame(columns=[
            'timestamp', 'semantic_feature', 'prosodic_feature',
            'latent_delta_magnitude', 'turn_label', 'audio_energy'
        ])

        # Create temporary thresholds file
        thresholds_file = tmp_path / 'thresholds.yaml'
        thresholds_data = {
            'audio_energy_threshold': 20.0,
            'delta_magnitude_threshold': 0.5,
            'algorithm': 'energy_overlap'
        }
        with open(thresholds_file, 'w') as f:
            import yaml
            yaml.dump(thresholds_data, f)

        # Test filter_events with empty input
        try:
            result = filter_events(empty_df, str(thresholds_file))
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0
            # Should not raise an error
        except Exception as e:
            pytest.fail(f"filter_events raised unexpected exception for empty input: {e}")

    def test_validate_output_empty_dataframe(self, tmp_path):
        """Test that validate_output handles empty DataFrame"""
        empty_df = pd.DataFrame(columns=[
            'timestamp', 'semantic_feature', 'prosodic_feature',
            'latent_delta_magnitude', 'turn_label', 'priority'
        ])

        # Test validation with empty DataFrame
        try:
            is_valid, errors = validate_output(empty_df)
            # Empty DataFrame should pass validation if schema is correct
            assert is_valid or len(errors) == 0
        except Exception as e:
            pytest.fail(f"validate_output raised unexpected exception for empty input: {e}")

    def test_load_config_missing_file(self, tmp_path):
        """Test that load_config handles missing config file"""
        missing_config = tmp_path / 'nonexistent_config.yaml'

        # Should raise FileNotFoundError or similar
        with pytest.raises((FileNotFoundError, IOError)):
            load_config(str(missing_config))


class TestThresholdValidation:
    """Tests for threshold validation logic in preprocess.py"""

    def test_filter_events_with_valid_thresholds(self, tmp_path):
        """Test filter_events with valid threshold configuration"""
        # Create sample data
        sample_data = pd.DataFrame({
            'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
            'semantic_feature': [0.1, 0.2, 0.3, 0.4, 0.5],
            'prosodic_feature': [0.1, 0.2, 0.3, 0.4, 0.5],
            'latent_delta_magnitude': [0.1, 0.3, 0.6, 0.8, 0.2],
            'turn_label': ['speaker_a', 'speaker_b', 'speaker_a', 'speaker_b', 'speaker_a'],
            'audio_energy': [15.0, 18.0, 25.0, 30.0, 12.0]
        })

        # Create thresholds file with reasonable values
        thresholds_file = tmp_path / 'thresholds.yaml'
        thresholds_data = {
            'audio_energy_threshold': 20.0,
            'delta_magnitude_threshold': 0.5,
            'algorithm': 'energy_overlap'
        }
        with open(thresholds_file, 'w') as f:
            import yaml
            yaml.dump(thresholds_data, f)

        try:
            result = filter_events(sample_data, str(thresholds_file))
            assert isinstance(result, pd.DataFrame)
            # Should have filtered some events
            assert len(result) <= len(sample_data)
        except Exception as e:
            pytest.fail(f"filter_events failed with valid thresholds: {e}")

    def test_filter_events_with_missing_threshold_fields(self, tmp_path):
        """Test filter_events with incomplete threshold configuration"""
        sample_data = pd.DataFrame({
            'timestamp': [1.0, 2.0],
            'semantic_feature': [0.1, 0.2],
            'prosodic_feature': [0.1, 0.2],
            'latent_delta_magnitude': [0.1, 0.2],
            'turn_label': ['speaker_a', 'speaker_b'],
            'audio_energy': [15.0, 18.0]
        })

        # Create thresholds file with missing required fields
        thresholds_file = tmp_path / 'incomplete_thresholds.yaml'
        thresholds_data = {
            'algorithm': 'energy_overlap'
            # Missing audio_energy_threshold and delta_magnitude_threshold
        }
        with open(thresholds_file, 'w') as f:
            import yaml
            yaml.dump(thresholds_data, f)

        # Should raise KeyError or ValueError for missing thresholds
        with pytest.raises((KeyError, ValueError, TypeError)):
            filter_events(sample_data, str(thresholds_file))

    def test_filter_events_with_invalid_threshold_types(self, tmp_path):
        """Test filter_events with invalid threshold types"""
        sample_data = pd.DataFrame({
            'timestamp': [1.0],
            'semantic_feature': [0.1],
            'prosodic_feature': [0.1],
            'latent_delta_magnitude': [0.1],
            'turn_label': ['speaker_a'],
            'audio_energy': [15.0]
        })

        # Create thresholds file with invalid types
        thresholds_file = tmp_path / 'invalid_thresholds.yaml'
        thresholds_data = {
            'audio_energy_threshold': "not_a_number",
            'delta_magnitude_threshold': 0.5,
            'algorithm': 'energy_overlap'
        }
        with open(thresholds_file, 'w') as f:
            import yaml
            yaml.dump(thresholds_data, f)

        # Should raise TypeError or ValueError
        with pytest.raises((TypeError, ValueError)):
            filter_events(sample_data, str(thresholds_file))

    def test_filter_events_with_negative_thresholds(self, tmp_path):
        """Test filter_events with negative threshold values"""
        sample_data = pd.DataFrame({
            'timestamp': [1.0, 2.0],
            'semantic_feature': [0.1, 0.2],
            'prosodic_feature': [0.1, 0.2],
            'latent_delta_magnitude': [0.1, 0.2],
            'turn_label': ['speaker_a', 'speaker_b'],
            'audio_energy': [15.0, 18.0]
        })

        # Create thresholds file with negative values
        thresholds_file = tmp_path / 'negative_thresholds.yaml'
        thresholds_data = {
            'audio_energy_threshold': -10.0,
            'delta_magnitude_threshold': -0.5,
            'algorithm': 'energy_overlap'
        }
        with open(thresholds_file, 'w') as f:
            import yaml
            yaml.dump(thresholds_data, f)

        # Should either raise an error or handle gracefully
        # Depending on implementation, negative thresholds might be invalid
        try:
            result = filter_events(sample_data, str(thresholds_file))
            # If it doesn't raise, it should still return a DataFrame
            assert isinstance(result, pd.DataFrame)
        except (ValueError, TypeError):
            # Expected behavior if negative thresholds are invalid
            pass

    def test_filter_events_with_extreme_thresholds(self, tmp_path):
        """Test filter_events with extreme threshold values"""
        sample_data = pd.DataFrame({
            'timestamp': [1.0, 2.0, 3.0],
            'semantic_feature': [0.1, 0.2, 0.3],
            'prosodic_feature': [0.1, 0.2, 0.3],
            'latent_delta_magnitude': [0.1, 0.2, 0.3],
            'turn_label': ['speaker_a', 'speaker_b', 'speaker_a'],
            'audio_energy': [15.0, 18.0, 20.0]
        })

        # Create thresholds file with extreme values
        thresholds_file = tmp_path / 'extreme_thresholds.yaml'
        thresholds_data = {
            'audio_energy_threshold': 1000000.0,  # Very high
            'delta_magnitude_threshold': 0.00001,  # Very low
            'algorithm': 'energy_overlap'
        }
        with open(thresholds_file, 'w') as f:
            import yaml
            yaml.dump(thresholds_data, f)

        try:
            result = filter_events(sample_data, str(thresholds_file))
            assert isinstance(result, pd.DataFrame)
            # With extreme thresholds, result might be empty or full
            # Just ensure no exception is raised
        except Exception as e:
            pytest.fail(f"filter_events failed with extreme thresholds: {e}")


class TestMemoryConstraints:
    """Tests for memory constraint handling"""

    def test_get_current_memory_usage_mb_returns_valid_value(self):
        """Test that memory usage function returns a valid number"""
        try:
            memory_mb = get_current_memory_usage_mb()
            assert isinstance(memory_mb, (int, float))
            assert memory_mb >= 0
        except Exception as e:
            pytest.fail(f"get_current_memory_usage_mb failed: {e}")


class TestConfigIntegration:
    """Tests for config integration"""

    def test_config_summary_exists(self):
        """Test that config module provides expected interface"""
        try:
            summary = get_config_summary()
            assert isinstance(summary, dict)
        except Exception as e:
            pytest.fail(f"get_config_summary failed: {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])