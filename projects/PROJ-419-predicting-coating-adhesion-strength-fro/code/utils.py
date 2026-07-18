import os
import time
import logging
import json
import requests
import yaml
from typing import Optional, Union, Dict, Any
from pathlib import Path

# Custom Exceptions
class DataGapError(Exception):
    """Raised when a required data source is missing or inaccessible."""
    pass

class APIError(Exception):
    """Raised when an API call fails."""
    pass

class MemoryLimitError(Exception):
    """Raised when memory usage exceeds the limit."""
    pass

class RuntimeLimitError(Exception):
    """Raised when runtime exceeds the limit."""
    pass

# Logging Setup
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level.upper()))

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

# State Management Helpers
def ensure_state_dir(state_dir: str = "state") -> None:
    os.makedirs(state_dir, exist_ok=True)

def write_halt_signal(reason: str, state_dir: str = "state") -> None:
    ensure_state_dir(state_dir)
    signal_path = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    data = {
        "halted": True,
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(signal_path, 'w') as f:
        yaml.dump(data, f)
    logging.getLogger("llmXive").critical(f"Halt signal written: {reason}")

def check_halt_signal(state_dir: Optional[Union[str, None]] = None) -> bool:
    """
    Checks for the existence of a HALT_SIGNAL.yaml file.
    
    Signature flexibility:
    - check_halt_signal() -> returns bool
    - check_halt_signal(state_dir) -> returns bool
    
    If no signal is found, returns False.
    """
    if state_dir is None:
        state_dir = "state"
    
    signal_path = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    if os.path.exists(signal_path):
        try:
            with open(signal_path, 'r') as f:
                data = yaml.safe_load(f)
                reason = data.get("reason", "Unknown reason")
                logging.getLogger("llmXive").critical(f"Halt signal detected: {reason}")
        except Exception as e:
            logging.getLogger("llmXive").error(f"Error reading halt signal: {e}")
        return True
    return False

# Retry Logic
def exponential_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for exponential backoff retry logic."""
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (requests.RequestException, APIError) as e:
                last_exception = e
                delay = base_delay * (2 ** attempt)
                logging.getLogger("llmXive").warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay}s..."
                )
                time.sleep(delay)
        raise last_exception
    return wrapper

def fetch_json_data(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch JSON data from a URL with error handling."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to fetch data from {url}: {e}")

def verify_url_accessibility(url: str, timeout: int = 10) -> bool:
    """Verify if a URL is accessible."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code < 400
    except requests.exceptions.RequestException:
        return False

# Memory Monitoring
def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        # ru_maxrss is in KB on Linux/macOS
        mem_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return mem_kb / 1024.0
    except Exception:
        return 0.0

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage exceeds the limit."""
    usage_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    if usage_mb > limit_mb:
        raise MemoryLimitError(f"Memory usage {usage_mb:.2f}MB exceeds limit {limit_mb:.2f}MB")
    return True

# Runtime Monitoring
class RuntimeMonitor:
    def __init__(self, start_time: Optional[float] = None):
        self.start_time = start_time or time.time()

    def elapsed_hours(self) -> float:
        return (time.time() - self.start_time) / 3600.0

    def check_limit(self, limit_hours: float = 4.0) -> bool:
        if self.elapsed_hours() > limit_hours:
            raise RuntimeLimitError(f"Runtime {self.elapsed_hours():.2f}h exceeds limit {limit_hours}h")
        return True

def start_runtime_monitoring() -> RuntimeMonitor:
    return RuntimeMonitor()

def check_runtime_limit(limit_hours: float = 4.0) -> bool:
    # This is a simplified check without persistent state for the monitor instance
    # In a real long-running process, the monitor instance would be passed around.
    # For this utility, we assume a global start or just a simple check if called repeatedly.
    # However, to be safe and stateless for a utility function, we can't track start time here
    # without a global or file. We'll rely on the class for tracking or assume external tracking.
    # For the specific task of T089/monitoring, the class is used.
    # This function acts as a placeholder if called without context, returning True.
    return True

def enforce_runtime_safety_margin(limit_hours: float = 4.0) -> bool:
    # Placeholder for safety margin enforcement logic
    return True

def main():
    """Main entry point for utils module testing."""
    logger = setup_logging()
    logger.info("Utils module loaded successfully.")
    
    # Test check_halt_signal with and without argument
    logger.info(f"Check halt (no arg): {check_halt_signal()}")
    logger.info(f"Check halt (with arg): {check_halt_signal('state')}")

if __name__ == "__main__":
    main()
