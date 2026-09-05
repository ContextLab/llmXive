import time
import logging
import sys
from typing import Callable, Any, Optional, Dict, Tuple
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

from src.config import get_config
from src.pipeline.logging_config import get_logger, time_execution, log_with_context

@dataclass
class TimeBudgetStatus:
    """Enum-like status for time budget checks."""
    OK: str = "ok"
    WARNING: str = "warning"
    CRITICAL: str = "critical"
    EXCEEDED: str = "exceeded"

class TimeBudgetMonitor:
    """Monitors wall-clock time and provides status updates."""

    def __init__(self, total_budget_seconds: float):
        self.total_budget_seconds = total_budget_seconds
        self.start_time = time.time()
        self.last_check_time = self.start_time
        self.logger = get_logger(__name__)

    def elapsed(self) -> float:
        return time.time() - self.start_time

    def remaining(self) -> float:
        return max(0.0, self.total_budget_seconds - self.elapsed())

    def status(self) -> TimeBudgetStatus:
        elapsed = self.elapsed()
        if elapsed > self.total_budget_seconds:
            return TimeBudgetStatus.EXCEEDED
        elif elapsed > 0.9 * self.total_budget_seconds:
            return TimeBudgetStatus.CRITICAL
        elif elapsed > 0.75 * self.total_budget_seconds:
            return TimeBudgetStatus.WARNING
        return TimeBudgetStatus.OK

    def log_progress(self, message: str = "Checking time budget"):
        elapsed = self.elapsed()
        remaining = self.remaining()
        status = self.status()
        self.logger.info(
            log_with_context(
                f"{message}: Elapsed={elapsed:.1f}s, Remaining={remaining:.1f}s, Status={status}"
            )
        )

def with_time_monitor(monitor: TimeBudgetMonitor, threshold_seconds: float = 7200):
    """
    Decorator to wrap a function with time monitoring and fallback logic.
    
    Args:
        monitor: The TimeBudgetMonitor instance.
        threshold_seconds: The time threshold (in seconds) after which subsampling is triggered.
                           Defaults to 2 hours (7200s).
    
    Returns:
        A decorator that wraps the target function.
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            start_func_time = time.time()
            
            # Check status before execution
            if monitor.status() == TimeBudgetStatus.EXCEEDED:
                raise TimeoutError(f"Time budget exceeded before starting {func.__name__}")
            
            # Execute the function
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                monitor.logger.error(f"Error in {func.__name__}: {e}")
                raise
            
            end_func_time = time.time()
            func_duration = end_func_time - start_func_time
            
            # Check if we crossed the threshold during execution
            if func_duration > threshold_seconds or monitor.elapsed() > threshold_seconds:
                monitor.logger.warning(
                    f"{func.__name__} took {func_duration:.1f}s or total elapsed is {monitor.elapsed():.1f}s. "
                    f"Triggering subsampling fallback logic for future operations."
                )
                # Return a flag or metadata indicating subsampling should be used next
                if isinstance(result, dict):
                    result['fallback_triggered'] = True
                else:
                    # Wrap result if it's not a dict to indicate fallback
                    result = {'data': result, 'fallback_triggered': True}
            
            return result
        return wrapper
    return decorator

def subsample_time_series(df: pd.DataFrame, frequency: int = 3) -> pd.DataFrame:
    """
    Subsamples a time-series DataFrame by keeping every N-th day.
    
    This is a fallback mechanism to reduce computational load when the
    analysis exceeds a time threshold.
    
    Args:
        df: DataFrame with a 'date' column (or index) and numeric data.
            Must have a datetime-like 'date' column or index.
        frequency: Keep every N-th day. Default is 3 (sample every 3rd day).
    
    Returns:
        A new DataFrame with subsampled rows.
    """
    if df.empty:
        return df

    logger = get_logger(__name__)
    logger.info(f"Subsampling time series with frequency={frequency}")

    # Ensure 'date' is datetime and set as index if it's a column
    if 'date' in df.columns:
        df_temp = df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['date'])
        df_temp = df_temp.set_index('date')
    else:
        df_temp = df.copy()
        # Assume index is datetime-like
        if not isinstance(df_temp.index, pd.DatetimeIndex):
            df_temp.index = pd.to_datetime(df_temp.index)

    # Resample or slice
    # Strategy: Sort by index, then take every Nth row
    # This preserves the time series structure better than random sampling
    df_sorted = df_temp.sort_index()
    
    # Calculate indices to keep
    indices_to_keep = df_sorted.index[::frequency]
    df_subsampled = df_sorted.loc[indices_to_keep]
    
    logger.info(f"Original shape: {df.shape}, Subsampled shape: {df_subsampled.shape}")
    
    return df_subsampled

def run_analysis_with_monitor(
    func: Callable,
    monitor: TimeBudgetMonitor,
    subsample_threshold: float = 7200,
    *args,
    **kwargs
) -> Any:
    """
    Runs an analysis function with time monitoring and automatic subsampling fallback.
    
    If the analysis function has not started or is about to run and the elapsed time
    suggests we are past the subsample threshold (e.g., 2 hours), it attempts to
    subsample the input data (if applicable) before running the function.
    
    Args:
        func: The analysis function to run.
        monitor: The TimeBudgetMonitor instance.
        subsample_threshold: Time in seconds (default 7200s / 2h) to trigger subsampling.
        *args, **kwargs: Arguments passed to func.
    
    Returns:
        The result of func.
    """
    logger = get_logger(__name__)

    # Check status before running
    status = monitor.status()
    if status == TimeBudgetStatus.EXCEEDED:
        raise TimeoutError(f"Analysis cannot start: Time budget exceeded ({monitor.elapsed():.1f}s)")

    # Prepare arguments, potentially subsampling if we are near the threshold
    # We check if the first argument is a DataFrame and if we are past the threshold
    new_args = list(args)
    subsampled = False

    if monitor.elapsed() > subsample_threshold and new_args:
        first_arg = new_args[0]
        if isinstance(first_arg, pd.DataFrame):
            logger.warning(f"Elapsed time {monitor.elapsed():.1f}s > {subsample_threshold}s. Triggering subsampling (every 3rd day).")
            new_args[0] = subsample_time_series(first_arg, frequency=3)
            subsampled = True
            monitor.log_progress("Subsampling triggered before analysis")

    # Update kwargs if a DataFrame is passed there (common pattern)
    if 'data' in kwargs and isinstance(kwargs['data'], pd.DataFrame):
        if monitor.elapsed() > subsample_threshold:
            logger.warning(f"Elapsed time {monitor.elapsed():.1f}s > {subsample_threshold}s. Triggering subsampling on 'data' kwarg.")
            kwargs['data'] = subsample_time_series(kwargs['data'], frequency=3)
            subsampled = True

    # Execute the function
    try:
        result = func(*new_args, **kwargs)
        if subsampled:
            if isinstance(result, dict):
                result['subsampled'] = True
            else:
                result = {'result': result, 'subsampled': True}
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

def main():
    """
    Entry point for testing the time monitoring and subsampling logic.
    This function is intended to be called by a test or a larger pipeline orchestration.
    """
    config = get_config()
    budget_seconds = config.get('wall_clock_budget_seconds', 300)
    
    # For demonstration, we set a larger budget if running in test mode
    # to allow the subsampling logic to be triggered manually if needed.
    # In production, this would be the strict 6-hour limit.
    if 'TEST_MODE' in os.environ:
        budget_seconds = 10000 

    monitor = TimeBudgetMonitor(budget_seconds)
    
    # Example usage pattern (would be called by the pipeline)
    # def heavy_analysis(data):
    #     ...
    #     return results
    
    # result = run_analysis_with_monitor(heavy_analysis, monitor, subsample_threshold=7200, data=df)
    
    print(f"Time Budget Monitor initialized with {budget_seconds}s budget.")
    print("Subsampling logic available via subsample_time_series() and run_analysis_with_monitor().")

if __name__ == "__main__":
    main()
