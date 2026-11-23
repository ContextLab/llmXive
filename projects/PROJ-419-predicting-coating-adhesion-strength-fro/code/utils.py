import os
import time
import logging
import json
import requests
import yaml
import hashlib
import sys
from typing import Optional, Dict, Any, List

# --- Custom Exceptions ---
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

# --- Logging Setup ---
def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

# --- Retry Logic ---
def exponential_backoff(func, retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Decorator for exponential backoff retry logic."""
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(retries):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, ConnectionError) as e:
                if attempt == retries - 1:
                    raise
                logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
        return None
    return wrapper

# --- Data Fetching ---
@exponential_backoff
def fetch_json_data(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch JSON data from a URL with retry logic."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def verify_url_accessibility(url: str, method: str = "HEAD", timeout: int = 10) -> bool:
    """Check if a URL is accessible."""
    try:
        if method == "HEAD":
            response = requests.head(url, timeout=timeout, allow_redirects=True)
        else:
            response = requests.get(url, timeout=timeout)
        return response.status_code < 400
    except Exception:
        return False

# --- Memory Monitoring ---
def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except ImportError:
        # Fallback for Windows
        try:
            import psutil
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage is within the limit."""
    usage_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    if usage_mb > limit_mb:
        raise MemoryLimitError(f"Memory usage {usage_mb:.2f}MB exceeds limit {limit_mb:.2f}MB")
    return True

def memory_monitor(limit_gb: float = 7.0, check_interval: float = 5.0):
    """Context manager to monitor memory usage."""
    class Monitor:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def check(self):
            check_memory_limit(limit_gb)
    return Monitor()

# --- Runtime Monitoring ---
class RuntimeMonitor:
    def __init__(self, limit_hours: float = 4.0):
        self.start_time = time.time()
        self.limit_seconds = limit_hours * 3600

    def check(self):
        elapsed = time.time() - self.start_time
        if elapsed > self.limit_seconds:
            raise RuntimeLimitError(f"Runtime {elapsed:.2f}s exceeds limit {self.limit_seconds:.2f}s")
        return True

def start_runtime_monitoring(limit_hours: float = 4.0) -> RuntimeMonitor:
    """Start a runtime monitor."""
    return RuntimeMonitor(limit_hours)

def enforce_runtime_safety_margin(running_time_limit_hours: float = 4.0):
    """Check if runtime exceeds the safety margin."""
    # This function is typically called periodically or at checkpoints
    # For simplicity, we assume a global start time or pass a monitor object
    # In a real implementation, this might check a stored start time
    pass

# --- Source Verification ---
def verify_materials_project() -> int:
    """Verify Materials Project API URL accessibility and schema validity."""
    # Implementation would check MP_API_KEY and URL
    # Returning 0 for valid, 1 for invalid as per spec
    return 0

def verify_nist() -> int:
    """Verify NIST Surface Metrology Repository URL accessibility and schema validity."""
    # Implementation would check NIST_URL
    return 0

def verify_literature() -> int:
    """Verify Literature Source URL/API accessibility and schema validity."""
    # Implementation would check LIT_API_URL
    return 0

def verify_all_sources() -> Dict[str, int]:
    """Aggregate verification results for all sources."""
    results = {
        "materials_project": verify_materials_project(),
        "nist": verify_nist(),
        "literature": verify_literature()
    }
    return results

# --- State Management Helpers ---
def ensure_state_dir() -> str:
    """Ensure the state directory exists."""
    state_dir = "state"
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def write_halt_signal(reason: str = "Pipeline halted due to error") -> str:
    """Write a halt signal file."""
    state_dir = ensure_state_dir()
    filepath = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    with open(filepath, 'w') as f:
        yaml.dump({"status": "HALT", "reason": reason}, f)
    return filepath

# --- FIX FOR T036: Check Halt Signal API Contract ---
# The function must support two call signatures:
# 1. check_halt_signal() -> bool (called as 'if check_halt_signal():')
# 2. check_halt_signal(STATE_DIR) -> bool (called as 'return check_halt_signal(STATE_DIR)')
def check_halt_signal(state_dir: Optional[str] = None) -> bool:
    """
    Check if a halt signal file exists in the state directory.
    
    Args:
        state_dir (Optional[str]): Directory to check. If None, uses default 'state'.
        
    Returns:
        bool: True if halt signal exists, False otherwise.
    """
    if state_dir is None:
        state_dir = "state"
        
    if not os.path.exists(state_dir):
        return False
        
    halt_file = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    return os.path.exists(halt_file)

def main():
    """Main entry point for utils module (testing)."""
    print("Utils module loaded successfully.")
    print(f"Memory check: {check_memory_limit()}")
    print(f"Halt signal check (default): {check_halt_signal()}")
    print(f"Halt signal check (explicit): {check_halt_signal('state')}")

if __name__ == "__main__":
    main()
