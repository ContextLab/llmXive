"""
Contract test for the TimeSeries schema.
Ensures the TimeSeries model validates data correctly.
"""
import pytest
from contracts.timeseries import TimeSeries

def test_timeseries_valid_data():
    """Test that valid data passes validation."""
    ts = TimeSeries(
        variable_name="GDP",
        source="FRED",
        frequency="monthly",
        unit="billions",
        data=[
            {"date": "2020-01-01", "value": 100.5},
            {"date": "2020-02-01", "value": 101.2}
        ]
    )
    assert ts.variable_name == "GDP"
    assert len(ts.get_dates()) == 2
    assert ts.get_values() == [100.5, 101.2]

def test_timeseries_missing_keys():
    """Test that data missing 'date' or 'value' fails."""
    with pytest.raises(ValueError):
        TimeSeries(
            variable_name="Test",
            source="TestSource",
            frequency="monthly",
            unit="units",
            data=[{"date": "2020-01-01"}]  # Missing 'value'
        )

def test_timeseries_empty_list():
    """Test that empty data list fails."""
    with pytest.raises(ValueError):
        TimeSeries(
            variable_name="Test",
            source="TestSource",
            frequency="monthly",
            unit="units",
            data=[]
        )
