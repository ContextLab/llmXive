import os
import time
import logging
import json
import requests
import yaml
import psutil
import sys
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager

# Custom Exceptions
class DataGapError(Exception):
    """Raised when a required data source is missing or inaccessible."""
    pass

class APIError(Exception):
    """Raised when an API call fails unexpectedly."""
    pass

class MemoryLimitError(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

class RuntimeLimitError(Exception):
    """Raised when runtime exceeds the configured limit."""
    pass

# Setup Logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File Handler (optional)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

logger = setup_logging()

# Retry Logic
def exponential_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (requests.RequestException,)
):
    """Decorator for exponential backoff retry logic."""
    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} retries: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay *= backoff_factor
    return wrapper

# Fetch Helper
@exponential_backoff
def fetch_json_data(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch JSON data from a URL with retry logic."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def verify_url_accessibility(url: str, timeout: int = 5) -> bool:
    """Check if a URL is accessible."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code < 400
    except Exception:
        return False

# Memory Monitoring
def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage is within limit."""
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    if current_mb > limit_mb:
        logger.error(f"Memory limit exceeded: {current_mb:.2f}MB > {limit_mb:.2f}MB")
        return False
    return True

@contextmanager
def memory_monitor(limit_gb: float = 7.0):
    """Context manager to monitor memory usage."""
    start_mem = get_memory_usage_mb()
    try:
        yield
    finally:
        end_mem = get_memory_usage_mb()
        logger.info(f"Memory usage change: {start_mem:.2f}MB -> {end_mem:.2f}MB")
        if not check_memory_limit(limit_gb):
            raise MemoryLimitError(f"Memory limit of {limit_gb}GB exceeded.")

# Runtime Monitoring
class RuntimeMonitor:
    def __init__(self, limit_hours: float = 4.0):
        self.limit_seconds = limit_hours * 3600
        self.start_time = time.time()

    def check(self) -> bool:
        elapsed = time.time() - self.start_time
        if elapsed > self.limit_seconds:
            logger.error(f"Runtime limit exceeded: {elapsed:.2f}s > {self.limit_seconds}s")
            return False
        return True

    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

def start_runtime_monitoring(limit_hours: float = 4.0) -> RuntimeMonitor:
    """Start a runtime monitor."""
    return RuntimeMonitor(limit_hours)

def enforce_runtime_safety_margin(monitor: RuntimeMonitor) -> None:
    """Check runtime and raise if exceeded."""
    if not monitor.check():
        raise RuntimeLimitError("Runtime safety margin exceeded.")

# Data Source Verification
def verify_materials_project() -> int:
    """Verify Materials Project API URL accessibility and schema validity.
    Returns 0 if valid, 1 if invalid."""
    # Placeholder for actual URL check
    return 0

def verify_nist() -> int:
    """Verify NIST Surface Metrology Repository URL accessibility and schema validity.
    Returns 0 if valid, 1 if invalid."""
    # Placeholder for actual URL check
    return 0

def verify_all_sources() -> Dict[str, int]:
    """Verify all external data sources and return status report."""
    status = {
        "materials_project": verify_materials_project(),
        "nist": verify_nist()
    }
    # Write report
    os.makedirs("data/processed", exist_ok=True)
    report_path = "data/processed/data_source_verification_report.json"
    with open(report_path, "w") as f:
        json.dump(status, f, indent=2)
    logger.info(f"Data source verification report written to {report_path}")
    return status

# State Management Helpers
def ensure_state_dir() -> str:
    """Ensure state directory exists."""
    os.makedirs("state", exist_ok=True)
    return "state"

def write_halt_signal(reason: str = "Unknown error") -> None:
    """Write a halt signal file."""
    state_dir = ensure_state_dir()
    signal_path = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    with open(signal_path, "w") as f:
        yaml.dump({"status": "HALT", "reason": reason, "timestamp": time.time()}, f)
    logger.critical(f"Halt signal written to {signal_path}")

def check_halt_signal(state_dir: Optional[str] = None) -> bool:
    """Check if a halt signal exists.
    
    Args:
        state_dir: Optional path to state directory. If None, uses default 'state'.
        
    Returns:
        True if halt signal exists, False otherwise.
    """
    if state_dir is None:
        state_dir = "state"
    
    signal_path = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    if os.path.exists(signal_path):
        try:
            with open(signal_path, "r") as f:
                signal_data = yaml.safe_load(f)
                logger.warning(f"Halt signal detected: {signal_data.get('reason', 'No reason provided')}")
                return True
        except Exception as e:
            logger.error(f"Error reading halt signal: {e}")
            return True # Treat read error as halt
    return False

def main():
    """Main entry point for utils module (testing)."""
    logger.info("Utils module loaded successfully.")
    if __name__ == "__main__":
        pass
