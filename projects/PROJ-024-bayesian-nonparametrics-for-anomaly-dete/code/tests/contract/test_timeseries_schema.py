"""Contract test for TimeSeries dataclass schema."""
import pytest
from datetime import datetime
from pathlib import Path
import numpy as np
from typing import List, Dict, Any, Optional

# Import from the correct path per API surface
from models.time_series import TimeSeries, TimeSeriesIterator

class TestTimeSeriesSchema:
    """Verify TimeSeries dataclass has required fields and types."""

    def test_timeseries_has_required_fields(self):
        """TimeSeries must have timestamp, values, and metadata fields."""
        ts = TimeSeries(
            timestamp=datetime(2024, 1, 1),
            values=np.array([1.0, 2.0, 3.0]),
            metadata={"source": "test"}
        )
        assert hasattr(ts, "timestamp")
        assert hasattr(ts, "values")
        assert hasattr(ts, "metadata")

    def test_timeseries_values_is_numpy_array(self):
        """TimeSeries.values must be a numpy array."""
        ts = TimeSeries(
            timestamp=datetime(2024, 1, 1),
            values=np.array([1.0, 2.0, 3.0]),
            metadata={}
        )
        assert isinstance(ts.values, np.ndarray)

    def test_timeseries_metadata_is_dict(self):
        """TimeSeries.metadata must be a dictionary."""
        ts = TimeSeries(
            timestamp=datetime(2024, 1, 1),
            values=np.array([1.0, 2.0, 3.0]),
            metadata={"key": "value"}
        )
        assert isinstance(ts.metadata, dict)

    def test_timeseries_can_serialize(self):
        """TimeSeries instances should be serializable to dict."""
        ts = TimeSeries(
            timestamp=datetime(2024, 1, 1),
            values=np.array([1.0, 2.0, 3.0]),
            metadata={"source": "test"}
        )
        from dataclasses import asdict
        serialized = asdict(ts)
        assert "timestamp" in serialized
        assert "values" in serialized
        assert "metadata" in serialized

    def test_timeseries_iterator_creation(self):
        """TimeSeriesIterator must be creatable from TimeSeries."""
        ts = TimeSeries(
            timestamp=datetime(2024, 1, 1),
            values=np.array([1.0, 2.0, 3.0]),
            metadata={}
        )
        iterator = TimeSeriesIterator(ts)
        assert iterator is not None

    def test_timeseries_values_shape(self):
        """TimeSeries values must support shape attribute."""
        ts = TimeSeries(
            timestamp=datetime(2024, 1, 1),
            values=np.array([1.0, 2.0, 3.0]),
            metadata={}
        )
        assert hasattr(ts.values, "shape")
        assert ts.values.shape[0] == 3
