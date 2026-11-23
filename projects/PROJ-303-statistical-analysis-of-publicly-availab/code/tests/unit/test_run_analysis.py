import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.pipeline.run_analysis import (
    TimeBudgetMonitor, 
    TimeBudgetStatus, 
    subsample_time_series, 
    run_analysis_with_monitor
)

class TestTimeBudgetMonitor:
    def test_initial_status_ok(self):
        monitor = TimeBudgetMonitor(100.0)
        assert monitor.status() == TimeBudgetStatus.OK

    def test_elapsed_time_calculation(self):
        monitor = TimeBudgetMonitor(100.0)
        time.sleep(0.1)
        assert 0.05 < monitor.elapsed() < 0.2

    def test_remaining_time_calculation(self):
        monitor = TimeBudgetMonitor(10.0)
        time.sleep(0.1)
        remaining = monitor.remaining()
        assert 9.8 < remaining < 10.0

    def test_status_exceeded(self):
        monitor = TimeBudgetMonitor(0.1)
        time.sleep(0.2)
        assert monitor.status() == TimeBudgetStatus.EXCEEDED

    def test_status_warning_threshold(self):
        # 75% of budget
        monitor = TimeBudgetMonitor(100.0)
        # Mock elapsed to be 76
        import src.pipeline.run_analysis as mod
        original_elapsed = mod.TimeBudgetMonitor.elapsed
        mod.TimeBudgetMonitor.elapsed = lambda self: 76.0
        
        assert mod.TimeBudgetMonitor(self=None).status() == TimeBudgetStatus.WARNING # type: ignore
        
        # Restore
        mod.TimeBudgetMonitor.elapsed = original_elapsed

class TestSubsampleTimeSeries:
    def create_dummy_df(self, days=100):
        dates = pd.date_range(start='2020-01-01', periods=days, freq='D')
        data = {
            'date': dates,
            'value': np.random.randn(days)
        }
        return pd.DataFrame(data)

    def test_subsampling_frequency_3(self):
        df = self.create_dummy_df(100)
        df_sub = subsample_time_series(df, frequency=3)
        
        # Should keep roughly 1/3 of the rows
        expected_count = 100 // 3
        assert len(df_sub) == expected_count or len(df_sub) == expected_count + 1
        
        # Check that dates are spaced by 3 days
        if len(df_sub) > 1:
            diffs = df_sub['date'].diff().dropna()
            # All diffs should be 3 days (or close due to freq)
            # Since we used .loc[::3], the index difference is 3 rows, which corresponds to 3 days
            assert all(d == pd.Timedelta(days=3) for d in diffs)

    def test_subsampling_empty_df(self):
        df = pd.DataFrame(columns=['date', 'value'])
        df['date'] = pd.to_datetime(df['date'])
        df_sub = subsample_time_series(df, frequency=3)
        assert df_sub.empty

    def test_subsampling_with_index(self):
        dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
        df = pd.DataFrame({'value': np.random.randn(100)}, index=dates)
        df_sub = subsample_time_series(df, frequency=3)
        
        assert len(df_sub) == 33 or len(df_sub) == 34
        assert isinstance(df_sub.index, pd.DatetimeIndex)

class TestRunAnalysisWithMonitor:
    def dummy_heavy_func(self, data):
        time.sleep(0.1)
        return {"result": "ok", "data_len": len(data)}

    def test_runs_successfully(self):
        monitor = TimeBudgetMonitor(1000.0)
        df = pd.DataFrame({'date': pd.date_range('2020-01-01', periods=10), 'value': range(10)})
        
        result = run_analysis_with_monitor(
            self.dummy_heavy_func, 
            monitor, 
            subsample_threshold=1.0, # High threshold so it doesn't trigger
            data=df
        )
        
        assert result['result'] == 'ok'
        assert result['data_len'] == 10
        assert 'subsampled' not in result or not result['subsampled']

    def test_triggers_subsampling(self):
        monitor = TimeBudgetMonitor(1000.0)
        df = pd.DataFrame({'date': pd.date_range('2020-01-01', periods=100), 'value': range(100)})
        
        # Mock elapsed to be > threshold
        import src.pipeline.run_analysis as mod
        original_elapsed = mod.TimeBudgetMonitor.elapsed
        mod.TimeBudgetMonitor.elapsed = lambda self: 10.0 # 10s > 1.0s threshold
        
        try:
            result = run_analysis_with_monitor(
                self.dummy_heavy_func, 
                monitor, 
                subsample_threshold=1.0, 
                data=df
            )
            
            assert result['result'] == 'ok'
            assert result['subsampled'] == True
            # Data should be subsampled (100 rows -> ~33)
            assert result['data_len'] < 50
        finally:
            mod.TimeBudgetMonitor.elapsed = original_elapsed