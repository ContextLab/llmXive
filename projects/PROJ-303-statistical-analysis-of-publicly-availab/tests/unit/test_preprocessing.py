import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import os
import sys

# Add the project root to the path to allow imports from src
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.preprocessing import calculate_thresholds, filter_stations, calculate_missing_ratio

class TestThresholdCalculationIsolation:
    """
    Verify that threshold calculation is strictly isolated to the training data (2000-2015).
    The test ensures that data from the test period (2019-2020) does not influence the calculated thresholds.
    """

    def test_thresholds_ignores_test_data(self):
        """
        Create a synthetic dataset with known values in training and test sets.
        Verify that the calculated threshold reflects ONLY the training data distribution,
        even if the test data contains extreme outliers.
        """
        # Create a DataFrame with a mix of training (2000-2015) and test (2019-2020) dates
        # We will use a single station 'STATION_A' for simplicity
        
        dates = []
        temps = []
        station_ids = []
        
        # Training data (2000-2015): Normal distribution, mean=20, std=5
        # We generate enough data to have a stable percentile
        np.random.seed(42)
        for year in range(2000, 2016):
            for month in range(1, 13):
                for day in range(1, 29): # Use 28 days to avoid leap year complications
                    dates.append(f"{year}-{month:02d}-{day:02d}")
                    station_ids.append("STATION_A")
                    temps.append(np.random.normal(20, 5))
        
        # Test data (2019-2020): Contains an extreme outlier (1000 degrees)
        # If the calculation incorrectly includes this, the 95th percentile will be skewed
        for year in range(2019, 2021):
            for month in range(1, 13):
                for day in range(1, 29):
                    dates.append(f"{year}-{month:02d}-{day:02d}")
                    station_ids.append("STATION_A")
                    # Normal values
                    temps.append(np.random.normal(20, 5))
            
        # Inject a massive outlier in the TEST period
        # This should NOT affect the threshold if isolation is working
        test_outlier_date = "2019-06-15"
        # Find the index of this date in our constructed list
        # Since we appended sequentially, we can calculate the offset
        # Training: 16 years * 12 months * 28 days = 5376 rows
        # Test starts at 5376. We want a specific date in 2019.
        # 2019 is the first year of test. Month 6, Day 15.
        # Offset within 2019: (6-1)*28 + (15-1) = 5*28 + 14 = 140 + 14 = 154
        # Absolute index: 5376 + 154 = 5530
        outlier_idx = 5376 + 154
        temps[outlier_idx] = 1000.0 
        
        df = pd.DataFrame({
            'station_id': station_ids,
            'date': dates,
            'tmax': temps
        })
        df['date'] = pd.to_datetime(df['date'])
        
        # Define training and test periods
        train_start = '2000-01-01'
        train_end = '2015-12-31'
        test_start = '2019-01-01'
        test_end = '2020-12-31'
        
        # Calculate thresholds using ONLY the training period
        # The function should accept date columns and range parameters
        thresholds = calculate_thresholds(
            df, 
            value_column='tmax', 
            station_column='station_id', 
            date_column='date',
            train_start=train_start,
            train_end=train_end,
            percentile=95
        )
        
        # Assert that a threshold was calculated
        assert 'STATION_A' in thresholds, "Threshold calculation failed for station"
        
        calculated_threshold = thresholds['STATION_A']
        
        # Theoretical check:
        # The training data is N(20, 5). The 95th percentile of N(20, 5) is approx 20 + 1.645*5 = 28.225
        # Even with a few variations in random generation, it should be close to 28.
        # The outlier (1000) is in the TEST set. If the calculation included the test set,
        # the 95th percentile would be significantly higher (likely > 100 because the outlier
        # would push the upper tail, or at least skew the distribution significantly if the
        # dataset size was smaller, but here the outlier is 1/10000th of the data, so it might
        # not shift the 95th percentile of the *combined* set much if the set is large enough,
        # BUT the logic must strictly filter by date).
        
        # Let's verify the isolation more strictly:
        # Calculate the 95th percentile of the training data manually
        train_mask = (df['date'] >= train_start) & (df['date'] <= train_end)
        manual_train_threshold = df.loc[train_mask, 'tmax'].quantile(0.95)
        
        # Verify the calculated threshold matches the manual calculation on training data
        assert np.isclose(calculated_threshold, manual_train_threshold, rtol=1e-5), \
            f"Threshold mismatch. Calculated: {calculated_threshold}, Expected (manual train only): {manual_train_threshold}"
        
        # Verify that the test data (including the outlier) was NOT used
        # If the function used the full dataset, the threshold would be different (though with N=5376+2400,
        # the single outlier might not shift the 95th percentile of the *combined* set drastically,
        # the strict requirement is that the code filters by date).
        # To be absolutely sure the code path filters, we can check that the logic inside
        # calculate_thresholds (if we could see it) filters. Since we are testing the output:
        # We rely on the assertion above: if the function filtered correctly, it equals the manual train-only calc.
        # If it didn't filter, it would equal the manual full-calc.
        
        full_mask = (df['date'] >= train_start) # Just to ensure we have data
        # Actually, let's calculate what the 95th percentile would be if we included the outlier
        # The outlier is 1000. The 95th percentile of the combined set (N=7776) with one outlier:
        # The outlier is at rank 7776. The 95th percentile is at rank 7776 * 0.95 = 7387.
        # The outlier is at rank 7776. So the outlier is ABOVE the 95th percentile of the combined set.
        # So the 95th percentile of the combined set would actually be the same as the 95th percentile
        # of the training set if the outlier is the absolute maximum and the training data is normal.
        # Wait, if the outlier is the max, it doesn't affect the 95th percentile if it's above that rank.
        # To make the test robust, we need an outlier that falls WITHIN the 95th percentile range of the combined set
        # OR we rely on the fact that the code MUST filter.
        
        # Let's try a different approach: Use a smaller dataset where the outlier shifts the 95th percentile
        # of the combined set significantly.
        
        # Re-generate small dataset
        small_dates = []
        small_temps = []
        small_stations = []
        
        # Training: 100 days, mean 20, std 5
        np.random.seed(123)
        for i in range(100):
            small_dates.append(f"2000-01-{(i % 28) + 1:02d}")
            small_stations.append("STATION_B")
            small_temps.append(np.random.normal(20, 5))
        
        # Test: 100 days, mean 20, std 5
        for i in range(100):
            small_dates.append(f"2019-01-{(i % 28) + 1:02d}")
            small_stations.append("STATION_B")
            small_temps.append(np.random.normal(20, 5))
        
        # Inject outlier in TEST set
        # We want this outlier to push the 95th percentile of the COMBINED set up.
        # Combined size = 200. 95th percentile index = 190.
        # If we set 10 values in the test set to 100, and the rest are normal.
        # The top 10 values of the combined set will be these 100s.
        # The 95th percentile (index 190) will be one of these 100s.
        # So the combined 95th percentile will be ~100.
        # The training 95th percentile will be ~28.
        
        # Replace the last 10 test entries with 100
        for i in range(10):
            idx = 100 + i # First 100 are training
            small_temps[idx] = 100.0
        
        small_df = pd.DataFrame({
            'station_id': small_stations,
            'date': small_dates,
            'tmax': small_temps
        })
        small_df['date'] = pd.to_datetime(small_df['date'])
        
        # Calculate threshold on training only
        small_thresholds = calculate_thresholds(
            small_df,
            value_column='tmax',
            station_column='station_id',
            date_column='date',
            train_start='2000-01-01',
            train_end='2015-12-31',
            percentile=95
        )
        
        calculated_small = small_thresholds['STATION_B']
        
        # Manual training 95th percentile
        small_train_mask = (small_df['date'] >= '2000-01-01') & (small_df['date'] <= '2015-12-31')
        manual_small_train = small_df.loc[small_train_mask, 'tmax'].quantile(0.95)
        
        # Manual combined 95th percentile (what it would be if we didn't filter)
        manual_small_combined = small_df['tmax'].quantile(0.95)
        
        # Assert that the calculated threshold matches the training-only calculation
        # and is significantly different from the combined calculation (which includes the outlier)
        assert np.isclose(calculated_small, manual_small_train, rtol=1e-5), \
            f"Threshold calculation did not isolate training data. Got {calculated_small}, expected {manual_small_train}"
        
        # The combined calculation should be much higher due to the 100s in the test set
        assert calculated_small < manual_small_combined, \
            f"Isolation failed: {calculated_small} is not less than combined {manual_small_combined}"

    def test_thresholds_excludes_test_period(self):
        """
        Verify that data strictly outside the training window is ignored.
        """
        # Create data where test period has a very different distribution
        dates = []
        temps = []
        stations = []
        
        # Training: 2000-2015, mean 10
        np.random.seed(99)
        for year in range(2000, 2016):
            for day in range(365):
                dates.append(f"{year}-{day//30%12+1:02d}-{day%28+1:02d}")
                stations.append("STATION_C")
                temps.append(np.random.normal(10, 2))
        
        # Test: 2019-2020, mean 100 (Huge shift)
        for year in range(2019, 2021):
            for day in range(365):
                dates.append(f"{year}-{day//30%12+1:02d}-{day%28+1:02d}")
                stations.append("STATION_C")
                temps.append(np.random.normal(100, 2))
        
        df = pd.DataFrame({
            'station_id': stations,
            'date': dates,
            'tmax': temps
        })
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate threshold
        thresholds = calculate_thresholds(
            df,
            value_column='tmax',
            station_column='station_id',
            date_column='date',
            train_start='2000-01-01',
            train_end='2015-12-31',
            percentile=95
        )
        
        # The threshold should be around 10 + 1.645*2 = 13.3
        # If it included test data, it would be around 103.3
        threshold = thresholds['STATION_C']
        
        assert threshold < 50, f"Threshold {threshold} is too high, likely included test data (mean 100)"
        assert threshold > 5, f"Threshold {threshold} is too low"
        
        # Verify against manual calculation on training data
        train_mask = (df['date'] >= '2000-01-01') & (df['date'] <= '2015-12-31')
        expected = df.loc[train_mask, 'tmax'].quantile(0.95)
        assert np.isclose(threshold, expected, rtol=1e-5), \
            f"Threshold {threshold} does not match manual training calculation {expected}"