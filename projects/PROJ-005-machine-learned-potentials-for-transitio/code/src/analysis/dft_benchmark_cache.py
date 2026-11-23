"""
Module to check for and validate the DFT benchmark cache file.

This module implements Task T036a: Check for DFT benchmark cache.
It checks if code/data/results/dft_benchmark_cache.json exists and is valid.
If it exists, it loads and verifies the structure.
If missing, it returns a status indicating T036b should run.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assuming the script is run from the project root or code/ directory
    current = Path.cwd()
    if current.name == 'code':
        return current.parent
    return current

def get_cache_path() -> Path:
    """Return the path to the DFT benchmark cache file."""
    project_root = get_project_root()
    return project_root / 'data' / 'results' / 'dft_benchmark_cache.json'

def load_cache(cache_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the DFT benchmark cache file.
    
    Args:
        cache_path: Path to the cache JSON file.
        
    Returns:
        Dictionary containing cache data, or None if file doesn't exist.
    """
    if not cache_path.exists():
        logger.info(f"Cache file not found: {cache_path}")
        return None
    
    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Successfully loaded cache from {cache_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in cache file {cache_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading cache file {cache_path}: {e}")
        raise

def validate_cache(cache_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate the structure of the DFT benchmark cache.
    
    Expected schema:
        {
            "reference_time_seconds": <float>
        }
        
    Args:
        cache_data: Dictionary containing cache data.
        
    Returns:
        Tuple of (is_valid, message)
    """
    required_keys = ["reference_time_seconds"]
    
    for key in required_keys:
        if key not in cache_data:
            return False, f"Missing required key: {key}"
    
    if not isinstance(cache_data["reference_time_seconds"], (int, float)):
        return False, "reference_time_seconds must be a numeric value"
    
    if cache_data["reference_time_seconds"] <= 0:
        return False, "reference_time_seconds must be positive"
    
    return True, "Cache is valid"

def check_cache() -> Dict[str, Any]:
    """
    Main function to check for DFT benchmark cache.
    
    Returns:
        Dictionary with status and data:
            {
                "status": "cached" | "missing",
                "data": <cache_data> | None,
                "validation": <validation_message> | None
            }
    """
    cache_path = get_cache_path()
    result = {
        "status": "missing",
        "data": None,
        "validation": None
    }
    
    # Check if file exists
    if not cache_path.exists():
        logger.info(f"DFT benchmark cache is missing at {cache_path}")
        result["status"] = "missing"
        return result
    
    # Load the cache
    try:
        cache_data = load_cache(cache_path)
        if cache_data is None:
            result["status"] = "missing"
            return result
        
        # Validate the cache
        is_valid, message = validate_cache(cache_data)
        result["validation"] = message
        
        if not is_valid:
            logger.warning(f"Cache validation failed: {message}")
            result["status"] = "invalid"
            return result
        
        result["status"] = "cached"
        result["data"] = cache_data
        logger.info(f"DFT benchmark cache is valid. Status: {result['status']}")
        return result
        
    except Exception as e:
        logger.error(f"Error checking cache: {e}")
        result["status"] = "error"
        result["validation"] = str(e)
        return result

def run_cache_check() -> int:
    """
    Run the cache check and print results.
    
    Returns:
        Exit code (0 for success, 1 for missing/invalid)
    """
    logger.info("Starting DFT benchmark cache check...")
    result = check_cache()
    
    print(f"Status: {result['status']}")
    if result['data']:
        print(f"Data: {result['data']}")
    if result['validation']:
        print(f"Validation: {result['validation']}")
    
    if result['status'] == 'cached':
        print("Cache is available and valid. T036b can be skipped.")
        return 0
    else:
        print("Cache is missing or invalid. T036b should be executed.")
        return 1

def main():
    """Entry point for the script."""
    sys.exit(run_cache_check())

if __name__ == "__main__":
    main()