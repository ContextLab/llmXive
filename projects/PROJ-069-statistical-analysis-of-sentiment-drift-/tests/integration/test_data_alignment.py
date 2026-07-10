"""
test_data_alignment.py

Integration test for data alignment logic.
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta


def test_monthly_alignment_logic():
    """
    Integration test: Verify that daily data can be resampled to monthly averages
    and that monthly data can be interpolated to fill gaps.
    """
    # Create synthetic daily sentiment data
    dates = pd.date_range(start="2023-01-01", end="2023-03-31", freq="D")
    sentiment_values = [float(i % 10) for i in range(len(dates))]
    sentiment_df = pd.DataFrame({"date": dates, "sentiment": sentiment_values})

    # Create synthetic monthly macro data with a gap
    macro_dates = [
        datetime(2023, 1, 1),
        datetime(2023, 3, 1)  # Skip February
    ]
    macro_values = [100.0, 102.0]
    macro_df = pd.DataFrame({"date": macro_dates, "gdp": macro_values})

    # Resample sentiment to monthly
    sentiment_df["date"] = pd.to_datetime(sentiment_df["date"])
    sentiment_monthly = sentiment_df.set_index("date").resample("ME").mean().reset_index()

    # Align macro data (linear interpolation)
    macro_df["date"] = pd.to_datetime(macro_df["date"])
    macro_interpolated = macro_df.set_index("date").asfreq("ME").interpolate(method="linear").reset_index()

    # Check that February is now present in macro data
    feb_data = macro_interpolated[macro_interpolated["date"].dt.month == 2]
    assert not feb_data.empty
    assert "gdp" in feb_data.columns
    # The interpolated value should be the average of Jan and Mar
    assert feb_data["gdp"].iloc[0] == pytest.approx(101.0, rel=1e-5)

    # Check that sentiment has monthly averages
    assert len(sentiment_monthly) == 3  # Jan, Feb, Mar
    assert "sentiment" in sentiment_monthly.columns
