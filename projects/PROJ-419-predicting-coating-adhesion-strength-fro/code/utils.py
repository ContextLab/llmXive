import os
import time
import logging
import json
import requests
import yaml
import psutil
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# Configure logging once to prevent duplicate handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/pipeline.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
MAX_ROWS = 5000
RAM_LIMIT_GB = 7
TIMEOUT_HOURS = 4
STATE_DIR = 'state'
HALT_SIGNAL_FILE = 'HALT_SIGNAL.yaml'

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_memory_limit(limit_gb: Optional[float] = None) -> bool:
    """Check if current memory usage exceeds the limit."""
    if limit_gb is None:
        limit_gb = RAM_LIMIT_GB
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    if current_mb > limit_mb:
        logger.warning(f"Memory usage {current_mb:.2f}MB exceeds limit {limit_mb:.2f}MB")
        return False
    return True

def log_memory_snapshot(step_name: str) -> None:
    """Log a memory usage snapshot for a specific step."""
    mem_mb = get_memory_usage_mb()
    logger.info(f"Memory Snapshot [{step_name}]: {mem_mb:.2f} MB")

def exponential_backoff(
    func,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exception_to_catch: Exception = requests.RequestException
):
    """Decorator for exponential backoff retry logic."""
    def wrapper(*args, **kwargs):
        delay = base_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exception_to_catch as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {delay:.2f}s...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
    return wrapper

@exponential_backoff
def fetch_json_data(url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Fetch JSON data from a URL with retry logic."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def verify_url_accessibility(url: str, timeout: int = 10) -> bool:
    """Verify if a URL is accessible."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"URL accessibility check failed for {url}: {e}")
        return False

def write_halt_signal(reason: str, details: Optional[Dict] = None) -> None:
    """Write a halt signal file to stop the pipeline."""
    os.makedirs(STATE_DIR, exist_ok=True)
    signal_data = {
        "status": "HALTED",
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details or {}
    }
    with open(os.path.join(STATE_DIR, HALT_SIGNAL_FILE), 'w') as f:
        yaml.dump(signal_data, f)
    logger.critical(f"Halt signal written: {reason}")

def check_materials_project_api() -> bool:
    """Check if Materials Project API is accessible."""
    url = "https://next-gen.materialsproject.org/api"
    return verify_url_accessibility(url)

def verify_materials_project_schema() -> bool:
    """Verify Materials Project API schema validity."""
    # Simplified check; in production, fetch a sample and validate schema
    return check_materials_project_api()

def check_nist_surface_metrology_api() -> bool:
    """Check if NIST Surface Metrology Repository is accessible."""
    url = "https://www.nist.gov/surface-metrology"
    return verify_url_accessibility(url)

def verify_nist_surface_metrology_schema() -> bool:
    """Verify NIST Surface Metrology Repository schema validity."""
    # Simplified check; in production, fetch a sample and validate schema
    return check_nist_surface_metrology_api()

def verify_nist_repository_and_halt() -> None:
    """Verify NIST repository and halt if inaccessible."""
    if not check_nist_surface_metrology_api():
        write_halt_signal("NIST Repository Unreachable", {"url": "NIST Surface Metrology"})
    if not verify_nist_surface_metrology_schema():
        write_halt_signal("NIST Schema Invalid", {"url": "NIST Surface Metrology"})

def verify_materials_project_and_halt() -> None:
    """Verify Materials Project API and halt if inaccessible."""
    if not check_materials_project_api():
        write_halt_signal("Materials Project API Unreachable", {"url": "Materials Project"})
    if not verify_materials_project_schema():
        write_halt_signal("Materials Project Schema Invalid", {"url": "Materials Project"})

def check_sample_size_power_analysis(n: int, min_required: int = 1000) -> bool:
    """Check if sample size meets power analysis requirements."""
    if n < min_required:
        logger.warning(f"Sample size {n} is below minimum required {min_required}")
        return False
    logger.info(f"Sample size {n} meets power analysis requirement (>= {min_required})")
    return True

def calculate_exclusion_ratio(total_records: int, missing_target_count: int) -> float:
    """Calculate the exclusion ratio of missing targets."""
    if total_records == 0:
        return 0.0
    return missing_target_count / total_records

def enforce_exclusion_ratio_threshold(ratio: float, threshold: float = 0.10) -> bool:
    """Enforce exclusion ratio threshold."""
    if ratio >= threshold:
        logger.error(f"Exclusion ratio {ratio:.2%} exceeds threshold {threshold:.2%}")
        write_halt_signal("Exclusion Ratio Exceeded", {"ratio": ratio, "threshold": threshold})
        return False
    logger.info(f"Exclusion ratio {ratio:.2%} is within threshold {threshold:.2%}")
    return True

def calculate_processing_success_rate(total_processed: int, successful: int) -> float:
    """Calculate the processing success rate."""
    if total_processed == 0:
        return 0.0
    return successful / total_processed

def enforce_success_rate_threshold(rate: float, threshold: float = 0.95) -> bool:
    """Enforce processing success rate threshold."""
    if rate < threshold:
        logger.error(f"Processing success rate {rate:.2%} is below threshold {threshold:.2%}")
        write_halt_signal("Success Rate Below Threshold", {"rate": rate, "threshold": threshold})
        return False
    logger.info(f"Processing success rate {rate:.2%} meets threshold {threshold:.2%}")
    return True

def main():
    """Main entry point for utils module (testing/demo)."""
    logger.info("Running utils module main...")
    log_memory_snapshot("Init")
    if not check_sample_size_power_analysis(1500):
        logger.warning("Power analysis check failed in demo")
    ratio = calculate_exclusion_ratio(1000, 50)
    enforce_exclusion_ratio_threshold(ratio)
    rate = calculate_processing_success_rate(1000, 980)
    enforce_success_rate_threshold(rate)

if __name__ == "__main__":
    main()