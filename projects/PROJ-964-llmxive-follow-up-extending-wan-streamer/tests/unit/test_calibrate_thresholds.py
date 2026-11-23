"""
Unit tests for T012b: Threshold Calibration.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from tasks.calibrate_thresholds import count_events, binary_search_calibration, load_config, save_config

class TestCountEvents:
    @pytest.fixture
    def sample_df(self):
        """Create a sample dataframe with known event characteristics."""
        data = {
            'audio_energy_db': [-40.0, -40.0, -40.0, -40.0, -40.0, -40.0, -40.0, -40.0, -40.0, -40.0, 
                                -10.0, -10.0, -10.0, -10.0, -10.0, 
                                -10.0, -10.0, -10.0, -10.0, -10.0,
                                -10.0, -10.0, -10.0, -10.0, -10.0,
                                -10.0, -10.0, -10.0, -10.0, -10.0,
                                -10.0, -10.0, -10.0, -10.0, -10.0,
                                -10.0, -10.0, -10.0, -10.0, -10.0,
                                -10.0, -10.0, -10.0, -10.0, -10.0,
                                -10.0, -10.0, -10.0, -10.0, -10.0],
            'latent_delta_magnitude': [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1,
                                       0.6, 0.6, 0.6, 0.6, 0.6,
                                       0.1, 0.1, 0.1, 0.1, 0.1,
                                       0.6, 0.6, 0.6, 0.6, 0.6,
                                       0.1, 0.1, 0.1, 0.1, 0.1,
                                       0.6, 0.6, 0.6, 0.6, 0.6,
                                       0.1, 0.1, 0.1, 0.1, 0.1,
                                       0.6, 0.6, 0.6, 0.6, 0.6,
                                       0.1, 0.1, 0.1, 0.1, 0.1,
                                       0.6, 0.6, 0.6, 0.6, 0.6,
                                       0.1, 0.1, 0.1, 0.1, 0.1]
        }
        return pd.DataFrame(data)

    def test_count_events_pause_detection(self, sample_df):
        """Test that pause detection works when threshold is high (e.g., -30)."""
        # Threshold -30: first 10 frames are < -30 (silent), next 40 are > -30 (speech).
        # 10 consecutive silent frames >= pause_duration_frames (10) -> 1 pause.
        # Interruptions: delta > 0.5 AND energy >= -30.
        # Frames 10-14, 20-24, 30-34, 40-44, 50-54 have energy -10 (>= -30) and delta 0.6 (> 0.5).
        # 5 groups of 5 interruptions = 25 interruptions.
        # Total = 1 + 25 = 26.
        count = count_events(sample_df, -30.0)
        assert count == 26

    def test_count_events_no_pause(self, sample_df):
        """Test that pause detection fails if silent segment is too short."""
        # Change one frame in the silent block to make it 9 frames
        df_mod = sample_df.copy()
        df_mod.loc[9, 'audio_energy_db'] = -20.0
        
        # Threshold -30: 9 frames silent (< 10 required) -> 0 pauses.
        # Interruptions remain 25.
        count = count_events(df_mod, -30.0)
        assert count == 25

    def test_count_events_no_interruption(self, sample_df):
        """Test that interruption detection fails if delta is low."""
        df_mod = sample_df.copy()
        df_mod['latent_delta_magnitude'] = 0.1 # All low delta
        
        # Threshold -30: 1 pause.
        # Interruptions: delta > 0.5? No. -> 0 interruptions.
        count = count_events(df_mod, -30.0)
        assert count == 1

class TestBinarySearch:
    @pytest.fixture
    def simple_df(self):
        # Create data where lowering threshold increases interruptions
        data = {
            'audio_energy_db': [-10.0] * 100, # All high energy
            'latent_delta_magnitude': [0.6] * 100 # All high delta
        }
        return pd.DataFrame(data)

    def test_finds_threshold_for_target(self, simple_df):
        """Test that search finds a threshold that meets the target."""
        # With -10 energy and 0.6 delta:
        # If threshold is -10: energy >= -10 (True) -> 100 interruptions.
        # If threshold is -20: energy >= -20 (True) -> 100 interruptions.
        # We need to find a threshold that gives >= 50 events.
        # Any threshold <= -10 should work.
        
        # Mock config to avoid file I/O in test
        import tasks.calibrate_thresholds as cal_module
        original_load = cal_module.load_config
        cal_module.load_config = lambda: {'latent_delta_magnitude': 0.5, 'pause_duration_frames': 10}
        
        try:
            result = binary_search_calibration(simple_df, -50.0, -5.0, 50, step_size=5.0, max_iterations=5)
            # Result should be a valid float
            assert isinstance(result, float)
            # Verify it actually yields >= 50
            count = count_events(simple_df, result)
            assert count >= 50
        finally:
            cal_module.load_config = original_load

    def test_handles_overshoot(self, simple_df):
        """Test behavior when target is easily met."""
        import tasks.calibrate_thresholds as cal_module
        original_load = cal_module.load_config
        cal_module.load_config = lambda: {'latent_delta_magnitude': 0.5, 'pause_duration_frames': 10}
        
        try:
            result = binary_search_calibration(simple_df, -50.0, -5.0, 5, step_size=5.0, max_iterations=5)
            assert isinstance(result, float)
        finally:
            cal_module.load_config = original_load
