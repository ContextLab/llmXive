"""
Unit tests for data entities.
"""
import pytest
from datetime import datetime, timedelta
from src.entities import EventDataset, SolarProxySeries


class TestEventDataset:
    """Tests for EventDataset class."""

    def test_create_empty_dataset(self):
        """Test creating an empty event dataset."""
        dataset = EventDataset(detector_id="IceCube")
        assert dataset.detector_id == "IceCube"
        assert dataset.total_events == 0
        assert dataset.events == []
        assert dataset.start_time is None
        assert dataset.end_time is None

    def test_create_dataset_with_events(self):
        """Test creating a dataset with events."""
        now = datetime.now()
        events = [
            {'timestamp': now, 'ra': 45.0, 'dec': 30.0, 'energy': 1.0},
            {'timestamp': now + timedelta(hours=1), 'ra': 50.0, 'dec': 35.0, 'energy': 2.0}
        ]
        dataset = EventDataset(detector_id="Auger", events=events)
        
        assert dataset.total_events == 2
        assert dataset.start_time == now
        assert dataset.end_time == now + timedelta(hours=1)

    def test_filter_by_time_range(self):
        """Test filtering events by time range."""
        base_time = datetime(2020, 1, 1)
        events = [
            {'timestamp': base_time, 'ra': 45.0, 'dec': 30.0, 'energy': 1.0},
            {'timestamp': base_time + timedelta(days=1), 'ra': 50.0, 'dec': 35.0, 'energy': 2.0},
            {'timestamp': base_time + timedelta(days=2), 'ra': 55.0, 'dec': 40.0, 'energy': 3.0}
        ]
        dataset = EventDataset(detector_id="IceCube", events=events)
        
        filtered = dataset.filter_by_time_range(
            base_time + timedelta(hours=1),
            base_time + timedelta(days=1, hours=12)
        )
        
        assert filtered.total_events == 1
        assert filtered.events[0]['ra'] == 50.0

    def test_get_ra_dec_lists(self):
        """Test extracting RA and Dec lists."""
        events = [
            {'timestamp': datetime.now(), 'ra': 45.0, 'dec': 30.0},
            {'timestamp': datetime.now(), 'ra': 50.0, 'dec': 35.0}
        ]
        dataset = EventDataset(detector_id="IceCube", events=events)
        
        ra, dec = dataset.get_ra_dec_lists()
        
        assert len(ra) == 2
        assert len(dec) == 2
        assert ra[0] == 45.0
        assert dec[0] == 30.0

    def test_to_summary_dict(self):
        """Test converting to summary dictionary."""
        now = datetime.now()
        events = [
            {'timestamp': now, 'ra': 45.0, 'dec': 30.0}
        ]
        dataset = EventDataset(detector_id="IceCube", events=events)
        
        summary = dataset.to_summary_dict()
        
        assert summary['detector_id'] == "IceCube"
        assert summary['total_events'] == 1
        assert 'start_time' in summary

    def test_empty_detector_id_raises_error(self):
        """Test that empty detector_id raises ValueError."""
        with pytest.raises(ValueError):
            EventDataset(detector_id="")


class TestSolarProxySeries:
    """Tests for SolarProxySeries class."""

    def test_create_empty_series(self):
        """Test creating an empty solar proxy series."""
        series = SolarProxySeries(proxy_type="sunspot_number", source="NOAA")
        assert series.proxy_type == "sunspot_number"
        assert series.source == "NOAA"
        assert len(series.timestamps) == 0
        assert len(series.values) == 0

    def test_create_series_with_data(self):
        """Test creating a series with data."""
        base_time = datetime(2020, 1, 1)
        timestamps = [base_time + timedelta(days=i) for i in range(5)]
        values = [10.0, 15.0, 20.0, 25.0, 30.0]
        
        series = SolarProxySeries(
            proxy_type="sunspot_number",
            source="NOAA",
            timestamps=timestamps,
            values=values,
            unit="count"
        )
        
        assert series.total_points == 5
        assert series.unit == "count"

    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched timestamp and value lengths raise ValueError."""
        with pytest.raises(ValueError):
            SolarProxySeries(
                proxy_type="sunspot_number",
                source="NOAA",
                timestamps=[datetime.now()],
                values=[10.0, 20.0]
            )

    def test_filter_by_time_range(self):
        """Test filtering series by time range."""
        base_time = datetime(2020, 1, 1)
        timestamps = [base_time + timedelta(days=i) for i in range(5)]
        values = [10.0, 15.0, 20.0, 25.0, 30.0]
        
        series = SolarProxySeries(
            proxy_type="sunspot_number",
            source="NOAA",
            timestamps=timestamps,
            values=values
        )
        
        filtered = series.filter_by_time_range(
            base_time + timedelta(days=1),
            base_time + timedelta(days=3)
        )
        
        assert len(filtered.timestamps) == 3
        assert filtered.values[0] == 15.0

    def test_to_summary_dict(self):
        """Test converting to summary dictionary."""
        base_time = datetime(2020, 1, 1)
        timestamps = [base_time + timedelta(days=i) for i in range(3)]
        values = [10.0, 15.0, 20.0]
        
        series = SolarProxySeries(
            proxy_type="solar_wind_speed",
            source="NGDC",
            timestamps=timestamps,
            values=values,
            unit="km/s"
        )
        
        summary = series.to_summary_dict()
        
        assert summary['proxy_type'] == "solar_wind_speed"
        assert summary['total_points'] == 3
        assert summary['unit'] == "km/s"

    def test_empty_proxy_type_raises_error(self):
        """Test that empty proxy_type raises ValueError."""
        with pytest.raises(ValueError):
            SolarProxySeries(proxy_type="", source="NOAA")

    def test_empty_source_raises_error(self):
        """Test that empty source raises ValueError."""
        with pytest.raises(ValueError):
            SolarProxySeries(proxy_type="sunspot_number", source="")