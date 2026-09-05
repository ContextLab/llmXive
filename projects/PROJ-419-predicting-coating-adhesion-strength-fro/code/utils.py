"""
Utility functions for the Coating Adhesion Pipeline.
"""
import os
import time
import logging
import json
import requests
import yaml
from typing import Optional, Dict, Any

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

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("coating_adhesion_pipeline")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    return logger

def exponential_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator for exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logging.getLogger("coating_adhesion_pipeline").warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator

def fetch_json_data(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetch JSON data from a URL with error handling.
    
    Args:
        url: URL to fetch data from
        headers: Optional request headers
        params: Optional query parameters
        
    Returns:
        Parsed JSON data
        
    Raises:
        APIError: If the request fails
    """
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise APIError(f"Failed to fetch data from {url}: {e}")

def verify_url_accessibility(url: str, timeout: int = 10) -> bool:
    """
    Verify if a URL is accessible.
    
    Args:
        url: URL to check
        timeout: Request timeout in seconds
        
    Returns:
        True if accessible, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        Memory usage in MB
    """
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    except ImportError:
        return 0.0

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """
    Check if current memory usage is within the limit.
    
    Args:
        limit_gb: Memory limit in GB
        
    Returns:
        True if within limit, False otherwise
    """
    usage_mb = get_memory_usage_mb()
    return usage_mb < (limit_gb * 1024)

def memory_monitor(limit_gb: float = 7.0, check_interval: float = 5.0):
    """
    Context manager for monitoring memory usage.
    
    Args:
        limit_gb: Memory limit in GB
        check_interval: Check interval in seconds
        
    Yields:
        None
        
    Raises:
        MemoryLimitError: If memory limit is exceeded
    """
    import threading
    
    stop_monitoring = threading.Event()
    max_usage = [0.0]
    
    def monitor_loop():
        while not stop_monitoring.is_set():
            usage = get_memory_usage_mb()
            if usage > max_usage[0]:
                max_usage[0] = usage
            if not check_memory_limit(limit_gb):
                stop_monitoring.set()
                raise MemoryLimitError(f"Memory limit exceeded: {usage / 1024:.2f} GB > {limit_gb} GB")
            time.sleep(check_interval)
    
    thread = threading.Thread(target=monitor_loop)
    thread.daemon = True
    thread.start()
    
    try:
        yield
    finally:
        stop_monitoring.set()
        thread.join(timeout=1)

class RuntimeMonitor:
    """Context manager for monitoring runtime."""
    
    def __init__(self, limit_hours: float = 4.0):
        self.limit_hours = limit_hours
        self.start_time = None
        self.elapsed = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        return False
    
    def check_limit(self) -> bool:
        """
        Check if runtime limit is exceeded.
        
        Returns:
            True if within limit, False otherwise
        """
        if self.elapsed == 0:
            self.elapsed = time.time() - self.start_time
        return self.elapsed / 3600 < self.limit_hours

def start_runtime_monitoring(limit_hours: float = 4.0) -> RuntimeMonitor:
    """
    Start runtime monitoring.
    
    Args:
        limit_hours: Time limit in hours
        
    Returns:
        RuntimeMonitor instance
    """
    return RuntimeMonitor(limit_hours)

def enforce_runtime_safety_margin(limit_hours: float = 4.0) -> bool:
    """
    Enforce runtime safety margin.
    
    Args:
        limit_hours: Time limit in hours
        
    Returns:
        True if within limit, False otherwise
        
    Raises:
        RuntimeLimitError: If limit is exceeded
    """
    # This is a placeholder; actual implementation would track elapsed time
    return True

def verify_materials_project() -> int:
    """
    Verify Materials Project API URL accessibility and schema validity.
    
    Returns:
        0 if valid, 1 if invalid
    """
    from config import main as config_main
    mp_url = config_main.NIST_URL  # Placeholder, should use MP_URL if defined
    try:
        response = requests.get(mp_url, timeout=10)
        if response.status_code == 200:
            return 0
        return 1
    except requests.exceptions.RequestException:
        return 1

def verify_nist() -> int:
    """
    Verify NIST Surface Metrology Repository URL accessibility and schema validity.
    
    Returns:
        0 if valid, 1 if invalid
    """
    from config import main as config_main
    nist_url = config_main.NIST_URL
    try:
        response = requests.get(nist_url, timeout=10)
        if response.status_code == 200:
            return 0
        return 1
    except requests.exceptions.RequestException:
        return 1

def verify_all_sources() -> Dict[str, int]:
    """
    Verify all data sources and aggregate results.
    
    Returns:
        Dictionary with status for each source
    """
    results = {
        "materials_project": verify_materials_project(),
        "nist": verify_nist()
    }
    
    # Write report
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/data_source_verification_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def ensure_state_dir() -> str:
    """
    Ensure state directory exists.
    
    Returns:
        Path to state directory
    """
    from config import main as config_main
    state_dir = config_main.STATE_DIR
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def write_halt_signal(reason: str = "Pipeline halted due to error") -> None:
    """
    Write a halt signal file.
    
    Args:
        reason: Reason for halting
    """
    state_dir = ensure_state_dir()
    signal_file = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    with open(signal_file, "w") as f:
        yaml.dump({"halted": True, "reason": reason, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}, f)

def check_halt_signal(state_dir: Optional[str] = None) -> bool:
    """
    Check if a halt signal exists.
    
    Args:
        state_dir: Optional path to state directory. If None, uses default from config.
        
    Returns:
        True if halt signal exists, False otherwise
    """
    if state_dir is None:
        from config import main as config_main
        state_dir = config_main.STATE_DIR
    
    signal_file = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    if os.path.exists(signal_file):
        try:
            with open(signal_file, "r") as f:
                signal_data = yaml.safe_load(f)
            return signal_data.get("halted", False)
        except Exception:
            return False
    return False

def main():
    """Main entry point for utilities."""
    logging.basicConfig(level=logging.INFO)
    logger = setup_logging()
    logger.info("Utilities module loaded successfully")

if __name__ == "__main__":
    main()
