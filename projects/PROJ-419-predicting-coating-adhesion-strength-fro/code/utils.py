import os
import time
import logging
import json
import requests
import yaml
import psutil
from typing import Optional, Dict, Any, List, Tuple
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SUCCESS_RATE_THRESHOLD = 0.95
EXCLUSION_RATIO_THRESHOLD = 0.10
MIN_SAMPLE_SIZE = 1000
MAX_ROWS = 5000
RAM_LIMIT_GB = 7
TIMEOUT_HOURS = 4
HALT_SIGNAL_PATH = "state/HALT_SIGNAL.yaml"

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def check_memory_limit(limit_gb: float = RAM_LIMIT_GB) -> bool:
    """Check if current memory usage exceeds limit."""
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    if current_mb > limit_mb:
        logger.warning(f"Memory usage {current_mb:.2f} MB exceeds limit {limit_mb:.2f} MB")
        return False
    return True

def log_memory_snapshot(step: str = "") -> None:
    """Log current memory usage snapshot."""
    usage = get_memory_usage_mb()
    logger.info(f"Memory Snapshot [{step}]: {usage:.2f} MB")

def exponential_backoff(
    func,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Execute function with exponential backoff retry logic."""
    delay = base_delay
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
    return None

def fetch_json_data(url: str, headers: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
    """Fetch JSON data from URL with retry logic."""
    def _do_fetch():
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    
    return exponential_backoff(_do_fetch)

def verify_url_accessibility(url: str, timeout: int = 10) -> bool:
    """Check if URL is accessible."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def write_halt_signal(reason: str, details: Optional[Dict] = None) -> None:
    """Write a halt signal file to stop pipeline execution."""
    os.makedirs(os.path.dirname(HALT_SIGNAL_PATH), exist_ok=True)
    signal_data = {
        "halt": True,
        "reason": reason,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "details": details or {}
    }
    with open(HALT_SIGNAL_PATH, 'w') as f:
        yaml.dump(signal_data, f, default_flow_style=False)
    logger.critical(f"Halt signal written: {reason}")

def check_halt_signal() -> Optional[Dict]:
    """Check if a halt signal exists."""
    if os.path.exists(HALT_SIGNAL_PATH):
        with open(HALT_SIGNAL_PATH, 'r') as f:
            return yaml.safe_load(f)
    return None

def verify_materials_project_schema(data: Dict) -> bool:
    """Verify Materials Project API response schema."""
    required_keys = ['data', 'response']
    if not all(k in data for k in required_keys):
        return False
    if not isinstance(data['data'], list):
        return False
    return True

def verify_nist_surface_metrology_schema(data: Dict) -> bool:
    """Verify NIST Surface Metrology Repository schema."""
    required_keys = ['results', 'count']
    if not all(k in data for k in required_keys):
        return False
    if not isinstance(data['results'], list):
        return False
    return True

def verify_materials_project_and_halt(url: str) -> bool:
    """Verify Materials Project URL and schema, halt if invalid."""
    logger.info(f"Verifying Materials Project URL: {url}")
    if not verify_url_accessibility(url):
        write_halt_signal("Data Gap: Materials Project URL inaccessible")
        return False
    
    data = fetch_json_data(url)
    if not data or not verify_materials_project_schema(data):
        write_halt_signal("Data Gap: Materials Project schema invalid")
        return False
    
    logger.info("Materials Project verification passed")
    return True

def verify_nist_repository_and_halt(url: str) -> bool:
    """Verify NIST Repository URL and schema, halt if invalid."""
    logger.info(f"Verifying NIST Repository URL: {url}")
    if not verify_url_accessibility(url):
        write_halt_signal("Data Gap: NIST Repository URL inaccessible")
        return False
    
    data = fetch_json_data(url)
    if not data or not verify_nist_surface_metrology_schema(data):
        write_halt_signal("Data Gap: NIST Repository schema invalid")
        return False
    
    logger.info("NIST Repository verification passed")
    return True

def check_sample_size_power_analysis(total_records: int) -> bool:
    """
    Check if sample size meets power analysis requirement (N >= 1000).
    
    Args:
        total_records: Total number of records in the dataset.
        
    Returns:
        True if N >= 1000, False otherwise.
    """
    if total_records < MIN_SAMPLE_SIZE:
        logger.warning(f"Sample size {total_records} is below power analysis threshold {MIN_SAMPLE_SIZE}")
        return False
    logger.info(f"Sample size check passed: {total_records} >= {MIN_SAMPLE_SIZE}")
    return True

def calculate_exclusion_ratio(df: pd.DataFrame, target_column: str = 'target') -> float:
    """
    Calculate the exclusion ratio: missing targets / total valid records.
    
    Args:
        df: DataFrame containing the data.
        target_column: Name of the target column to check for missing values.
        
    Returns:
        The exclusion ratio (float between 0 and 1).
    """
    total_records = len(df)
    if total_records == 0:
        return 0.0
    
    missing_targets = df[target_column].isna().sum()
    ratio = missing_targets / total_records
    logger.info(f"Exclusion ratio calculated: {ratio:.4f} ({missing_targets}/{total_records})")
    return ratio

def enforce_exclusion_ratio_threshold(ratio: float, threshold: float = EXCLUSION_RATIO_THRESHOLD) -> bool:
    """
    Enforce the exclusion ratio threshold (< 10%).
    
    Args:
        ratio: The calculated exclusion ratio.
        threshold: Maximum allowed ratio (default 0.10).
        
    Returns:
        True if ratio < threshold, False otherwise.
    """
    if ratio >= threshold:
        logger.error(f"Exclusion ratio {ratio:.4f} exceeds threshold {threshold}")
        write_halt_signal(
            "Data Quality Gate: Exclusion Ratio Too High",
            {"ratio": ratio, "threshold": threshold}
        )
        return False
    logger.info(f"Exclusion ratio check passed: {ratio:.4f} < {threshold}")
    return True

def calculate_processing_success_rate(df: pd.DataFrame, valid_columns: List[str]) -> float:
    """
    Calculate the processing success rate.
    
    Success rate is defined as: (records with all valid columns populated) / (total records).
    
    Args:
        df: DataFrame containing the processed data.
        valid_columns: List of column names that must be non-null for a record to be considered successful.
        
    Returns:
        The processing success rate (float between 0 and 1).
    """
    total_records = len(df)
    if total_records == 0:
        return 0.0
    
    # Filter to only the specified valid columns
    subset_df = df[valid_columns]
    
    # Count rows where all specified columns are non-null
    successful_records = subset_df.dropna(how='any').shape[0]
    
    success_rate = successful_records / total_records
    logger.info(f"Processing success rate calculated: {success_rate:.4f} ({successful_records}/{total_records})")
    return success_rate

def enforce_success_rate_threshold(success_rate: float, threshold: float = SUCCESS_RATE_THRESHOLD) -> bool:
    """
    Enforce the processing success rate threshold (>= 95%).
    
    Args:
        success_rate: The calculated processing success rate.
        threshold: Minimum required rate (default 0.95).
        
    Returns:
        True if success_rate >= threshold, False otherwise.
    """
    if success_rate < threshold:
        logger.error(f"Processing success rate {success_rate:.4f} is below threshold {threshold}")
        write_halt_signal(
            "Data Quality Gate: Processing Success Rate Too Low",
            {"success_rate": success_rate, "threshold": threshold}
        )
        return False
    logger.info(f"Processing success rate check passed: {success_rate:.4f} >= {threshold}")
    return True

def main():
    """Main entry point for utils module (standalone testing)."""
    logger.info("Running utils module standalone test...")
    
    # Test memory functions
    mem = get_memory_usage_mb()
    logger.info(f"Current memory: {mem:.2f} MB")
    
    # Test URL verification (example with a known public API)
    # Note: In real usage, use actual project URLs
    # verify_url_accessibility("https://api.materialsproject.org")
    
    logger.info("Utils module test completed.")

if __name__ == "__main__":
    main()