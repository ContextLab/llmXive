import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple, Union
import pandas as pd

# Constants for logging configuration
LOG_DIR = Path("logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry to prevent duplicate handlers
_loggers: dict = {}

def setup_logging(
    log_level: int = logging.INFO,
    log_dir: Optional[Union[str, Path]] = None,
    enable_file_handler: bool = True,
    enable_console_handler: bool = True
) -> None:
    """
    Configure the root logger with file and console handlers.
    
    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_dir: Directory to store log files. Defaults to 'logs' in project root.
        enable_file_handler: Whether to add a file handler.
        enable_console_handler: Whether to add a console handler.
    """
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates on re-runs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    if enable_console_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(console_handler)
    
    if enable_file_handler:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger, reusing existing instances if possible.
    
    Args:
        name: Name of the logger (e.g., 'ingestion', 'analysis')
    
    Returns:
        Configured Logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    # Don't propagate to root if we've already configured specific handlers
    # to avoid double logging if root has handlers too.
    logger.propagate = True 
    _loggers[name] = logger
    return logger

def setup_ingestion_logging(
    log_dir: Optional[Union[str, Path]] = None,
    log_level: int = logging.INFO
) -> Tuple[logging.Logger, logging.Logger, logging.Logger]:
    """
    Specialized logging setup for the ingestion pipeline (US1).
    Creates specific loggers for different ingestion steps.
    
    Args:
        log_dir: Directory for log files.
        log_level: Logging level.
    
    Returns:
        Tuple of (main_logger, alignment_logger, outlier_logger)
    """
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)
    
    # Ensure root is set up if not already
    if not logging.getLogger().handlers:
        setup_logging(log_level=log_level, log_dir=log_dir)
    
    main_logger = get_logger("ingestion.main")
    alignment_logger = get_logger("ingestion.alignment")
    outlier_logger = get_logger("ingestion.outliers")
    
    # Ensure these specific loggers have handlers if the root doesn't cover them
    # (This is a safety net; usually propagate=True handles it)
    if not main_logger.handlers:
        main_logger.addHandler(logging.StreamHandler(sys.stdout))
        main_logger.addHandler(logging.FileHandler(log_dir / "ingestion_main.log"))
        main_logger.setLevel(log_level)
    
    if not alignment_logger.handlers:
        alignment_logger.addHandler(logging.StreamHandler(sys.stdout))
        alignment_logger.addHandler(logging.FileHandler(log_dir / "ingestion_alignment.log"))
        alignment_logger.setLevel(log_level)
    
    if not outlier_logger.handlers:
        outlier_logger.addHandler(logging.StreamHandler(sys.stdout))
        outlier_logger.addHandler(logging.FileHandler(log_dir / "ingestion_outliers.log"))
        outlier_logger.setLevel(log_level)
    
    return main_logger, alignment_logger, outlier_logger

def detect_ph_outliers(
    df: pd.DataFrame,
    pH_col: str = "pH",
    low_threshold: float = 1.0,
    high_threshold: float = 10.0,
    edge_low: float = 2.0,
    edge_high_start: float = 8.5,
    edge_high_end: float = 10.0
) -> pd.DataFrame:
    """
    Detects pH outliers and flags edge ranges per FR-006.
    
    Flags:
    - 'outlier': pH < 1.0 or pH > 10.0
    - 'edge_range_low': 1.0 <= pH < 2.0
    - 'edge_range_high': 8.5 <= pH <= 10.0
    
    Args:
        df: DataFrame containing pH data.
        pH_col: Column name for pH values.
        low_threshold: Absolute lower bound for valid pH.
        high_threshold: Absolute upper bound for valid pH.
        edge_low: Lower bound of the low edge range.
        edge_high_start: Start of the high edge range.
        edge_high_end: End of the high edge range.
    
    Returns:
        DataFrame with added 'pH_status' column.
    """
    if pH_col not in df.columns:
        raise ValueError(f"Column '{pH_col}' not found in DataFrame")
    
    def classify_ph(val):
        if pd.isna(val):
            return "missing"
        if val < low_threshold or val > high_threshold:
            return "outlier"
        if val < edge_low:
            return "edge_range_low"
        if edge_high_start <= val <= edge_high_end:
            return "edge_range_high"
        return "normal"
    
    df = df.copy()
    df["pH_status"] = df[pH_col].apply(classify_ph)
    return df

def calculate_ph_heterogeneity(
    df: pd.DataFrame,
    timestamp_col: str = "timestamp",
    pH_col: str = "pH",
    window_minutes: int = 15
) -> pd.DataFrame:
    """
    Calculates pH heterogeneity (SD) within a ±15 minute window per FR-001.1.
    
    Args:
        df: DataFrame with timestamp and pH columns.
        timestamp_col: Name of the timestamp column.
        pH_col: Name of the pH column.
        window_minutes: Time window in minutes (default 15).
    
    Returns:
        DataFrame with 'pH_heterogeneity' (SD) column added.
    """
    if timestamp_col not in df.columns or pH_col not in df.columns:
        raise ValueError(f"Required columns '{timestamp_col}' and '{pH_col}' not found")
    
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    df = df.sort_values(timestamp_col)
    
    # Calculate rolling SD with a time-based window
    # We use a centered rolling window: [t - 15min, t + 15min]
    # pandas rolling with 'min_periods' handles the edge cases
    window_str = f"{window_minutes}min"
    
    # Calculate SD for each point based on neighbors within the window
    # Using a rolling window approach is efficient for this
    # Note: Standard rolling is [t-window, t]. To get symmetric ±15, we can
    # calculate the rolling SD on the sorted data.
    # A strict symmetric window requires a custom loop or groupby if data is dense.
    # For efficiency with large datasets, we approximate with a forward/backward pass
    # or use the standard rolling window which is sufficient for "within window" logic
    # in most time-series contexts unless strict symmetry is mandated by FR.
    # FR-001.1 says "within ±15 min window".
    
    # Efficient approach: Group by time buckets or use rolling with a larger window
    # and then filter? No, rolling is best.
    # Let's use a custom function for strict symmetry if needed, but standard rolling
    # is usually acceptable for "heterogeneity" metrics in this context.
    # To be precise with ±15min, we calculate the SD of all points in [t-15, t+15].
    
    heterogeneity = []
    times = df[timestamp_col].values
    phs = df[pH_col].values
    
    # Vectorized approach might be complex for exact symmetric windows.
    # Using a loop for correctness on the "symmetric" requirement is safer for science.
    # Optimization: If data is sorted, we can use two pointers.
    
    left = 0
    right = 0
    n = len(df)
    
    # Pre-allocate
    sd_values = [0.0] * n
    
    for i in range(n):
        current_time = times[i]
        
        # Expand right to include all points <= current_time + 15min
        while right < n and times[right] <= current_time + pd.Timedelta(minutes=window_minutes):
            right += 1
        
        # Shrink left to exclude all points < current_time - 15min
        while left < n and times[left] < current_time - pd.Timedelta(minutes=window_minutes):
            left += 1
        
        # Slice is [left, right)
        window_ph = phs[left:right]
        if len(window_ph) > 1:
            sd_values[i] = pd.Series(window_ph).std()
        else:
            sd_values[i] = 0.0
    
    df["pH_heterogeneity"] = sd_values
    return df

def main():
    """
    Entry point for testing logging configuration.
    """
    setup_logging(log_level=logging.DEBUG)
    logger = get_logger("utils.main")
    logger.info("Utils module logging initialized successfully.")
    
    # Test ingestion logging
    main_log, align_log, outlier_log = setup_ingestion_logging(log_level=logging.INFO)
    main_log.info("Ingestion main logger ready.")
    align_log.info("Ingestion alignment logger ready.")
    outlier_log.info("Ingestion outliers logger ready.")

if __name__ == "__main__":
    main()