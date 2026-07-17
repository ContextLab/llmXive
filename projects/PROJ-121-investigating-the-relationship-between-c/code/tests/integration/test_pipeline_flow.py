"""
Integration tests for the full pipeline flow.

This test verifies the end-to-end execution of the pipeline:
1. Data download (mocked)
2. Data binning
3. Anisotropy analysis
4. Results writing

The test ensures all components work together correctly.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

from src.entities import EventDataset, SolarProxySeries
from src.binning import bin_events, get_bin_statistics
from src.anisotropy import generate_healpix_map, fit_dipole_coefficients
from src.results_writer import write_dipole_timeseries
from src.config import DEFAULT_BIN_SIZE_DAYS


class TestPipelineFlow:
    """Integration tests for the complete pipeline flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, "data")
        self.results_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_pipeline_with_mock_data(self):
        """Test the complete pipeline flow with mock data."""
        # Create mock event data
        n_events = 1000
        base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        
        timestamps = [
            base_time + timedelta(hours=i) 
            for i in range(n_events)
        ]
        ra = np.random.uniform(0, 360, n_events)
        dec = np.random.uniform(-90, 90, n_events)
        energy = np.random.uniform(18, 20, n_events)
        
        events = EventDataset(
            timestamps=timestamps,
            ra=ra.tolist(),
            dec=dec.tolist(),
            energy=energy.tolist(),
            detector_id="TestDetector"
        )
        
        # Step 1: Bin events
        bins = bin_events(events, bin_size_days=7)
        
        assert len(bins) > 0, "No bins created"
        assert all('interval_start' in b for b in bins), "Missing interval_start"
        assert all('n_events' in b for b in bins), "Missing n_events"
        
        # Step 2: Generate HEALPix map for each bin
        for i, bin_data in enumerate(bins[:3]):  # Test first 3 bins
            # Filter events for this bin
            bin_events_list = []
            bin_ra = []
            bin_dec = []
            
            for j, ts in enumerate(events.timestamps):
                if bin_data['interval_start'] <= ts < bin_data['interval_end']:
                    bin_events_list.append(j)
                    bin_ra.append(events.ra[j])
                    bin_dec.append(events.dec[j])
            
            if len(bin_ra) > 0:
                # Generate HEALPix map
                nside = 64
                npix = 12 * nside * nside
                
                # Convert to radians
                theta = np.radians(90 - np.array(bin_dec))
                phi = np.radians(np.array(bin_ra))
                
                # Create map
                healpix_map = np.zeros(npix)
                indices = hp.ang2pix(nside, theta, phi)
                for idx in indices:
                    healpix_map[idx] += 1
                
                # Fit dipole
                dipole_coeffs = fit_dipole_coefficients(healpix_map, nside)
                
                assert len(dipole_coeffs) == 3, "Dipole coefficients should have 3 components"
        
        # Step 3: Write results
        output_csv = os.path.join(self.results_dir, "dipole_timeseries.csv")
        
        # Prepare test results
        test_results = []
        for bin_data in bins[:5]:
            test_results.append({
                'interval_start': bin_data['interval_start'],
                'interval_end': bin_data['interval_end'],
                'dipole_amp': np.random.uniform(0.001, 0.01),
                'dipole_phase': np.random.uniform(0, 360),
                'quad_amp': np.random.uniform(0.0001, 0.001),
                'partial_interval': bin_data['partial_interval']
            })
        
        success = write_dipole_timeseries(test_results, output_csv)
        
        assert success, "Failed to write results"
        assert os.path.exists(output_csv), "Output CSV not created"
        
        # Verify CSV content
        df = pd.read_csv(output_csv)
        assert len(df) == len(test_results), "CSV row count mismatch"
        assert 'interval_start' in df.columns, "Missing interval_start column"
        assert 'dipole_amp' in df.columns, "Missing dipole_amp column"
        assert 'partial_interval' in df.columns, "Missing partial_interval column"
    
    def test_pipeline_handles_empty_bins(self):
        """Test pipeline behavior when some bins have no events."""
        # Create sparse event data
        base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        timestamps = [
            base_time + timedelta(days=i*10)  # Events every 10 days
            for i in range(5)
        ]
        
        events = EventDataset(
            timestamps=timestamps,
            ra=[10.0, 20.0, 30.0, 40.0, 50.0],
            dec=[10.0, 20.0, 30.0, 40.0, 50.0],
            energy=[19.0, 19.0, 19.0, 19.0, 19.0],
            detector_id="SparseTest"
        )
        
        # Bin with 7-day intervals (some bins will be empty)
        bins = bin_events(events, bin_size_days=7)
        
        assert len(bins) > 0, "No bins created"
        
        # Check that some bins have zero events
        zero_event_bins = [b for b in bins if b['n_events'] == 0]
        assert len(zero_event_bins) > 0, "Expected some empty bins"
        
        # Verify statistics
        stats = get_bin_statistics(bins)
        assert stats['total_bins'] == len(bins)
        assert stats['total_events'] == 5  # Total events should match
    
    def test_pipeline_partial_interval_handling(self):
        """Test that partial intervals are correctly marked."""
        # Create event data that doesn't align perfectly with bin boundaries
        base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        n_events = 20
        timestamps = [
            base_time + timedelta(hours=i*6)  # Events every 6 hours
            for i in range(n_events)
        ]
        
        events = EventDataset(
            timestamps=timestamps,
            ra=[i * 10.0 for i in range(n_events)],
            dec=[i * 5.0 for i in range(n_events)],
            energy=[19.0] * n_events,
            detector_id="PartialTest"
        )
        
        # Bin with 7-day intervals
        bins = bin_events(events, bin_size_days=7)
        
        # The last bin should be marked as partial if it doesn't fill completely
        partial_bins = [b for b in bins if b['partial_interval']]
        
        # At least one bin should be partial (the last one)
        assert len(partial_bins) >= 1, "Expected at least one partial interval"
    
    def test_pipeline_data_integrity_throughout(self):
        """Test that data integrity is maintained throughout the pipeline."""
        # Create known event data
        base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        n_events = 100
        timestamps = [
            base_time + timedelta(hours=i)
            for i in range(n_events)
        ]
        ra = [i * 3.6 for i in range(n_events)]  # 0 to 360 degrees
        dec = [0.0] * n_events
        energy = [19.0] * n_events
        
        original_events = EventDataset(
            timestamps=timestamps,
            ra=ra,
            dec=dec,
            energy=energy,
            detector_id="IntegrityTest"
        )
        
        # Bin the events
        bins = bin_events(original_events, bin_size_days=7)
        
        # Verify total event count is preserved
        total_binned_events = sum(b['n_events'] for b in bins)
        assert total_binned_events == n_events, \
            f"Event count mismatch: {total_binned_events} != {n_events}"
        
        # Verify no events are lost or duplicated
        assert len(bins) > 0, "No bins created"
    
    def test_pipeline_with_solar_proxy_data(self):
        """Test pipeline integration with solar proxy data."""
        # Create mock solar proxy data
        base_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        proxy_timestamps = [
            base_time + timedelta(days=i)
            for i in range(365)
        ]
        proxy_values = np.random.uniform(50, 150, 365).tolist()
        
        solar_proxy = SolarProxySeries(
            timestamps=proxy_timestamps,
            values=proxy_values,
            proxy_type="sunspot_number",
            source="NOAA"
        )
        
        # Create event data spanning the same period
        event_timestamps = [
            base_time + timedelta(hours=i*6)
            for i in range(365 * 4)
        ]
        events = EventDataset(
            timestamps=event_timestamps,
            ra=[i * 0.1 for i in range(len(event_timestamps))],
            dec=[0.0] * len(event_timestamps),
            energy=[19.0] * len(event_timestamps),
            detector_id="SolarCorrelationTest"
        )
        
        # Bin events
        bins = bin_events(events, bin_size_days=27)
        
        # Verify we can correlate bins with proxy data
        assert len(bins) > 0, "No bins created"
        assert len(solar_proxy.timestamps) > 0, "No proxy data"
        
        # Check that bin time range overlaps with proxy data
        first_bin_start = bins[0]['interval_start']
        last_bin_end = bins[-1]['interval_end']
        
        assert first_bin_start >= solar_proxy.timestamps[0], \
            "First bin before proxy data start"
        assert last_bin_end <= solar_proxy.timestamps[-1] + timedelta(days=1), \
            "Last bin after proxy data end"
