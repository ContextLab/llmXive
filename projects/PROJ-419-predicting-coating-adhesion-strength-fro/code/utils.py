import os
import time
import logging
import json
import requests
import yaml
from typing import Optional, Dict, Any, List, Tuple
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
NIST_SURFACE_METROLOGY_URL = os.getenv(
    "NIST_SURFACE_METROLOGY_URL",
    "https://www.nist.gov/materials/surface-metrology-repository"
)
NIST_EXPECTED_SCHEMA_KEYS = {"surface_roughness", "method", "sample_id"}
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

def exponential_backoff(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """Retry a function with exponential backoff."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            wait_time = (2 ** attempt) * 2
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
    logger.error(f"All {max_retries} attempts failed for {func.__name__}")
    raise last_exception

def fetch_json_data(url: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Fetch JSON data from a URL with timeout and error handling."""
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from {url}: {e}")
        return None

def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def check_memory_limit(limit_gb: float = 7.0) -> bool:
    """Check if current memory usage is within limit."""
    usage_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024
    if usage_mb > limit_mb:
        logger.warning(f"Memory usage {usage_mb:.2f}MB exceeds limit {limit_mb:.2f}MB")
        return False
    return True

def log_memory_snapshot(tag: str = ""):
    """Log current memory usage."""
    usage = get_memory_usage_mb()
    logger.info(f"Memory Snapshot [{tag}]: {usage:.2f} MB")

def verify_url_accessibility(url: str) -> bool:
    """Verify if a URL is accessible via HTTP GET."""
    try:
        response = requests.head(url, timeout=TIMEOUT_SECONDS)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"URL {url} is not accessible: {e}")
        return False

def write_halt_signal(reason: str, source: str):
    """Write a HALT_SIGNAL.yaml to the state directory."""
    state_dir = "state"
    os.makedirs(state_dir, exist_ok=True)
    signal_path = os.path.join(state_dir, "HALT_SIGNAL.yaml")
    
    signal_data = {
        "status": "HALTED",
        "reason": reason,
        "source": source,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    
    with open(signal_path, 'w') as f:
        yaml.dump(signal_data, f, default_flow_style=False)
    logger.error(f"Halt signal written to {signal_path}: {reason}")

def check_materials_project_api() -> bool:
    """Check basic accessibility of Materials Project API (placeholder for T009 logic)."""
    # T009 implementation would go here
    return True

def verify_materials_project_schema(data: Dict[str, Any]) -> bool:
    """Verify schema of Materials Project data (placeholder for T009 logic)."""
    # T009 implementation would go here
    return True

def check_nist_surface_metrology_api() -> bool:
    """
    Check accessibility of the NIST Surface Metrology Repository URL.
    Returns True if accessible, False otherwise.
    """
    try:
        logger.info(f"Checking accessibility of NIST URL: {NIST_SURFACE_METROLOGY_URL}")
        response = requests.head(NIST_SURFACE_METROLOGY_URL, timeout=TIMEOUT_SECONDS)
        if response.status_code == 200:
            logger.info("NIST URL is accessible (HEAD request successful).")
            return True
        else:
            logger.error(f"NIST URL returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to NIST URL: {e}")
        return False

def verify_nist_surface_metrology_schema() -> bool:
    """
    Verify the schema of the NIST Surface Metrology Repository.
    Attempts to fetch a sample record or metadata and validates expected keys.
    Returns True if schema is valid, False otherwise.
    """
    # Attempt to fetch data. Since the exact endpoint might vary, we try a standard query
    # or a known metadata endpoint. If the main URL is just a landing page, we might need
    # a specific API endpoint. For this implementation, we assume the URL provided 
    # supports a JSON response or we fetch a known sample structure.
    
    # Fallback: Try to fetch a known sample or metadata if the URL is a landing page.
    # In a real scenario, this URL would be a specific API endpoint like /api/v1/samples.
    # For robustness, we try to GET the URL and parse if it's JSON, or check headers.
    
    try:
        logger.info(f"Verifying schema for NIST URL: {NIST_SURFACE_METROLOGY_URL}")
        # Try GET to see if it returns JSON or HTML (landing page)
        response = requests.get(NIST_SURFACE_METROLOGY_URL, timeout=TIMEOUT_SECONDS)
        
        if response.status_code != 200:
            logger.error(f"NIST URL returned non-200 status: {response.status_code}")
            return False

        # Check if content is JSON
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            data = response.json()
            # If it's a list, check the first item
            if isinstance(data, list) and len(data) > 0:
                sample = data[0]
            elif isinstance(data, dict):
                sample = data
            else:
                logger.error("NIST response is not a JSON object or list.")
                return False
            
            # Validate expected keys
            missing_keys = NIST_EXPECTED_SCHEMA_KEYS - set(sample.keys())
            if missing_keys:
                logger.error(f"NIST schema validation failed. Missing keys: {missing_keys}")
                return False
            
            logger.info("NIST schema validation passed.")
            return True
        else:
            # If it's HTML (landing page), we might not be able to validate schema programmatically
            # without a specific API endpoint. We treat this as a schema verification failure
            # because we cannot guarantee the data structure without a JSON endpoint.
            logger.error("NIST URL does not return JSON. Cannot validate schema programmatically.")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during schema verification: {e}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from NIST URL: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during schema verification: {e}")
        return False

def verify_nist_repository_and_halt() -> bool:
    """
    Full verification of NIST Surface Metrology Repository.
    Checks accessibility and schema validity.
    If either check fails, writes HALT_SIGNAL.yaml and returns False.
    """
    logger.info("Starting NIST Surface Metrology Repository verification (Task T010)...")
    
    # 1. Check Accessibility
    if not check_nist_surface_metrology_api():
        reason = "NIST Surface Metrology Repository URL is not accessible."
        write_halt_signal(reason, "T010-NIST-Accessibility")
        return False
    
    # 2. Check Schema
    if not verify_nist_surface_metrology_schema():
        reason = "NIST Surface Metrology Repository schema is invalid or missing expected keys."
        write_halt_signal(reason, "T010-NIST-Schema")
        return False
    
    logger.info("NIST Surface Metrology Repository verification successful.")
    return True

def verify_materials_project_and_halt() -> bool:
    """
    Full verification of Materials Project API (Placeholder for T009 logic).
    Checks accessibility and schema validity.
    If either check fails, writes HALT_SIGNAL.yaml and returns False.
    """
    # Placeholder implementation for T009 completion
    logger.info("Materials Project verification (T009) - Placeholder logic.")
    return True

def check_sample_size_power_analysis(n_samples: int, min_required: int = 1000) -> bool:
    """Check if sample size meets power analysis requirements."""
    if n_samples < min_required:
        logger.warning(f"Sample size {n_samples} is below required {min_required}.")
        return False
    return True

def calculate_exclusion_ratio(total_records: int, excluded_records: int) -> float:
    """Calculate the ratio of excluded records."""
    if total_records == 0:
        return 0.0
    return excluded_records / total_records

def calculate_processing_success_rate(total_records: int, processed_records: int) -> float:
    """Calculate the processing success rate."""
    if total_records == 0:
        return 0.0
    return processed_records / total_records

def enforce_success_rate_threshold(success_rate: float, threshold: float = 0.95) -> bool:
    """Enforce success rate threshold."""
    if success_rate < threshold:
        logger.error(f"Success rate {success_rate:.2f} is below threshold {threshold}.")
        return False
    return True

def main():
    """Main entry point for utility scripts."""
    logger.info("Running utils.py main...")
    # Example usage
    verify_nist_repository_and_halt()

if __name__ == "__main__":
    main()