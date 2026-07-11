"""
Unit tests for the pipeline module.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Adjust import path for local testing if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.pipeline import run_pipeline, process_interval
from src.entities import EventDataset
import numpy as np


class TestPipelineOrchestration:
    """Tests for the main pipeline orchestration logic."""

    @patch('src.pipeline.load_all_data')
    @patch('src.pipeline.bin_events')
    @patch('src.pipeline.generate_healpix_map')
    @patch('src.pipeline.fit_dipole_coefficients')
    @patch('src.pipeline.calculate_anisotropy_stats')
    @patch('src.pipeline.fetch_solar_proxy')
    @patch('src.pipeline.os.makedirs')
    @patch('src.pipeline.open', new_callable=mock_open)
    def test_run_pipeline_success(
        self,
        mock_open_file,
        mock_makedirs,
        mock_fetch_proxy,
        mock_calc_stats,
        mock_fit_dipole,
        mock_gen_map,
        mock_bin_events,
        mock_load_data
    ):
        """Test a successful pipeline run with mocked dependencies."""
        
        # Setup mock data
        mock_events = MagicMock(spec=EventDataset)
        mock_events.timestamps = [
            datetime(2020, 1, 1, tzinfo=timezone.utc),
            datetime(2020, 1, 2, tzinfo=timezone.utc)
        ]
        mock_events.ra = np.array([0.0, 1.0])
        mock_events.dec = np.array([0.0, 1.0])
        
        mock_load_data.return_value = mock_events
        mock_bin_events.return_value = mock_events
        
        mock_map = np.zeros(12 * 64 * 64) # Nside=64
        mock_gen_map.return_value = mock_map
        
        mock_dipole = np.array([0.1, 0.2, 0.3])
        mock_fit_dipole.return_value = mock_dipole
        
        mock_stats = {
            'dipole_amplitude': 0.5,
            'dipole_phase': 1.5,
            'quadrupole_amplitude': 0.1
        }
        mock_calc_stats.return_value = mock_stats
        
        mock_fetch_proxy.return_value = {'mean_value': 100.0}

        # Run pipeline
        results = run_pipeline(
            bin_size_days=1,
            start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2020, 1, 3, tzinfo=timezone.utc),
            output_dir="data/results"
        )

        # Assertions
        assert len(results) == 2 # Two 1-day intervals
        assert results[0]['dipole_amplitude'] == 0.5
        assert results[0]['solar_proxy_mean'] == 100.0
        assert mock_makedirs.called
        assert mock_open_file.called

    @patch('src.pipeline.load_all_data')
    def test_run_pipeline_no_data(self, mock_load_data):
        """Test pipeline fails gracefully when no data is loaded."""
        mock_load_data.return_value = None
        
        with pytest.raises(RuntimeError, match="No cosmic ray data loaded"):
            run_pipeline()

    @patch('src.pipeline.load_all_data')
    def test_run_pipeline_empty_dataset(self, mock_load_data):
        """Test pipeline fails gracefully when dataset is empty."""
        mock_events = MagicMock(spec=EventDataset)
        mock_events.timestamps = []
        mock_load_data.return_value = mock_events
        
        with pytest.raises(ValueError, match="No events found"):
            run_pipeline()

    @patch('src.pipeline.load_all_data')
    @patch('src.pipeline.bin_events')
    def test_run_pipeline_partial_interval(self, mock_bin_events, mock_load_data):
        """Test that partial intervals are correctly identified."""
        mock_events = MagicMock(spec=EventDataset)
        mock_events.timestamps = [datetime(2020, 1, 1, tzinfo=timezone.utc)]
        mock_events.ra = np.array([0.0])
        mock_events.dec = np.array([0.0])
        
        mock_load_data.return_value = mock_events
        mock_bin_events.return_value = mock_events

        # 2 days data, 3 day bin -> should result in 1 partial interval
        results = run_pipeline(
            bin_size_days=3,
            start_date=datetime(2020, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2020, 1, 3, tzinfo=timezone.utc),
            output_dir="data/results"
        )

        assert len(results) == 1
        assert results[0]['partial_interval'] is True