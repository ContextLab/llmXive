import os
import time
import logging
import json
import requests
import yaml
import psutil
import traceback
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# Constants
MAX_ROWS = 5000
RAM_LIMIT_GB = 7
TIMEOUT_HOURS = 4
SUCCESS_RATE_THRESHOLD = 0.95
EXCLUSION_RATIO_THRESHOLD = 0.10
MIN_SAMPLE_SIZE = 1000

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)

def check_memory_limit(limit_gb: float = RAM_LIMIT_GB) -> bool:
    """Check if current memory usage is within limit."""
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    return current_mb < limit_mb

def log_memory_snapshot(stage: str = "Unknown") -> None:
    """Log current memory usage snapshot."""
    mem_mb = get_memory_usage_mb()
    logger.info(f"Memory Snapshot [{stage}]: {mem_mb:.2f} MB")

def exponential_backoff(
    func,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple = (requests.exceptions.RequestException,)
):
    """Decorator for exponential backoff retry logic."""
    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries reached. Last error: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
    return wrapper

@exponential_backoff
def fetch_json_data(url: str, timeout: int = 30) -> Optional[Dict]:
    """Fetch JSON data from a URL with retry logic."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def verify_url_accessibility(url: str, timeout: int = 10) -> bool:
    """Check if a URL is accessible."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"URL accessibility check failed for {url}: {e}")
        return False

def write_halt_signal(reason: str, state_dir: str = "state") -> None:
    """Write a halt signal file."""
    os.makedirs(state_dir, exist_ok=True)
    signal_file = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    signal_data = {
        "halted": True,
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open(signal_file, 'w') as f:
        yaml.dump(signal_data, f, default_flow_style=False)
    logger.critical(f"Halt signal written: {signal_file}")

def check_halt_signal(state_dir: str = "state") -> Optional[Dict]:
    """Check for a halt signal file."""
    signal_file = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    if os.path.exists(signal_file):
        try:
            with open(signal_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to read halt signal: {e}")
    return None

def verify_materials_project_schema(url: str, timeout: int = 30) -> bool:
    """Verify Materials Project API URL and basic schema validity."""
    if not verify_url_accessibility(url, timeout):
        logger.error(f"Materials Project URL not accessible: {url}")
        return False
    try:
        data = fetch_json_data(url, timeout)
        # Basic schema check: expect 'data' or 'results' key
        if not isinstance(data, dict) or not any(key in data for key in ['data', 'results', 'docs']):
            logger.error(f"Invalid schema from Materials Project: {data}")
            return False
        return True
    except Exception as e:
        logger.error(f"Schema verification failed for Materials Project: {e}")
        return False

def verify_nist_surface_metrology_schema(url: str, timeout: int = 30) -> bool:
    """Verify NIST Surface Metrology Repository URL and basic schema validity."""
    if not verify_url_accessibility(url, timeout):
        logger.error(f"NIST URL not accessible: {url}")
        return False
    try:
        data = fetch_json_data(url, timeout)
        # Basic schema check: expect list or dict with records
        if not isinstance(data, (dict, list)) or (isinstance(data, dict) and len(data) == 0):
            logger.error(f"Invalid schema from NIST: {data}")
            return False
        return True
    except Exception as e:
        logger.error(f"Schema verification failed for NIST: {e}")
        return False

def verify_materials_project_and_halt(url: str, timeout: int = 30) -> None:
    """Verify Materials Project URL and halt if invalid."""
    if not verify_materials_project_schema(url, timeout):
        write_halt_signal("Data Gap: Materials Project URL invalid or inaccessible")
        raise SystemExit(1)

def verify_nist_repository_and_halt(url: str, timeout: int = 30) -> None:
    """Verify NIST URL and halt if invalid."""
    if not verify_nist_surface_metrology_schema(url, timeout):
        write_halt_signal("Data Gap: NIST Repository URL invalid or inaccessible")
        raise SystemExit(1)

def check_sample_size_power_analysis(n: int, min_n: int = MIN_SAMPLE_SIZE) -> bool:
    """
    Check if sample size meets minimum requirement for statistical power.
    Returns True if n >= min_n, False otherwise.
    """
    if n < min_n:
        logger.warning(f"Sample size {n} is below minimum threshold {min_n}")
        return False
    logger.info(f"Sample size check passed: {n} >= {min_n}")
    return True

def calculate_exclusion_ratio(total_records: int, excluded_records: int) -> float:
    """
    Calculate the exclusion ratio (missing targets / total valid).
    Returns the ratio as a float between 0 and 1.
    """
    if total_records == 0:
        return 0.0
    ratio = excluded_records / total_records
    logger.info(f"Exclusion Ratio: {excluded_records}/{total_records} = {ratio:.4f}")
    return ratio

def enforce_exclusion_ratio_threshold(ratio: float, threshold: float = EXCLUSION_RATIO_THRESHOLD) -> bool:
    """
    Enforce exclusion ratio threshold.
    Returns True if ratio < threshold, False otherwise.
    Raises SystemExit if threshold is exceeded.
    """
    if ratio >= threshold:
        msg = f"Exclusion Ratio {ratio:.4f} exceeds threshold {threshold:.4f}. Halting."
        logger.error(msg)
        write_halt_signal(f"Data Quality: Exclusion ratio too high ({ratio:.4f} >= {threshold:.4f})")
        raise SystemExit(1)
    logger.info(f"Exclusion Ratio check passed: {ratio:.4f} < {threshold:.4f}")
    return True

def calculate_processing_success_rate(total_processed: int, successful_records: int) -> float:
    """
    Calculate the processing success rate.
    Returns the rate as a float between 0 and 1.
    """
    if total_processed == 0:
        return 0.0
    rate = successful_records / total_processed
    logger.info(f"Processing Success Rate: {successful_records}/{total_processed} = {rate:.4f}")
    return rate

def enforce_success_rate_threshold(rate: float, threshold: float = SUCCESS_RATE_THRESHOLD) -> bool:
    """
    Enforce processing success rate threshold (>= 95%).
    Returns True if rate >= threshold, False otherwise.
    Raises SystemExit if threshold is not met.
    """
    if rate < threshold:
        msg = f"Processing Success Rate {rate:.4f} is below threshold {threshold:.4f}. Halting."
        logger.error(msg)
        write_halt_signal(f"Data Quality: Processing success rate too low ({rate:.4f} < {threshold:.4f})")
        raise SystemExit(1)
    logger.info(f"Processing Success Rate check passed: {rate:.4f} >= {threshold:.4f}")
    return True

def main():
    """Main entry point for utils module (demo/validation)."""
    logger.info("Running utils module validation...")
    
    # Test memory functions
    mem = get_memory_usage_mb()
    logger.info(f"Current memory: {mem:.2f} MB")
    
    # Test success rate calculation
    total = 1000
    success = 950
    rate = calculate_processing_success_rate(total, success)
    enforce_success_rate_threshold(rate)
    
    # Test exclusion ratio
    total_rec = 1000
    excluded = 50
    ratio = calculate_exclusion_ratio(total_rec, excluded)
    enforce_exclusion_ratio_threshold(ratio)
    
    logger.info("Utils validation complete.")

if __name__ == "__main__":
    main()