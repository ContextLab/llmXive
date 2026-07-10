"""
Contract test for the RecessionPeriod schema.
"""
import pytest
from contracts.recession_periods import RecessionPeriod

def test_recession_period_valid():
    """Test valid recession period."""
    rp = RecessionPeriod(
        start_date="2020-02-01",
        end_date="2020-04-01",
        notes="COVID-19 Recession"
    )
    assert rp.start_date == "2020-02-01"
    assert rp.to_range()[1].month == 4

def test_recession_period_invalid_order():
    """Test that end date before start date fails."""
    with pytest.raises(ValueError):
        RecessionPeriod(
            start_date="2020-04-01",
            end_date="2020-02-01"
        )

def test_recession_period_invalid_format():
    """Test that invalid date format fails."""
    with pytest.raises(ValueError):
        RecessionPeriod(
            start_date="2020/02/01",
            end_date="2020-04-01"
        )