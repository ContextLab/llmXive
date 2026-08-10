"""
Memory usage monitoring for the ceramic Weibull modulus prediction pipeline.
Implements checks to prevent exceeding the configured memory limit (6GB default).
"""
import os
import sys
import logging
import gc
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available. Memory monitoring will be limited.")

from config import get_int_config, initialize_config, get_project_config

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.
    
    Returns:
        float: Memory usage in GB. Returns 0.0 if psutil is unavailable.
    """
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil not installed. Cannot measure memory usage accurately.")
        return 0.0
    
    try:
        process = psutil.Process(os.getpid())
        memory_bytes = process.memory_info().rss
        memory_gb = memory_bytes / (1024 ** 3)
        return memory_gb
    except Exception as e:
        logger.error(f"Failed to get memory usage: {e}")
        return 0.0

def check_memory_limit(limit_gb: Optional[float] = None, fail_on_exceed: bool = True) -> Dict[str, Any]:
    """
    Check if current memory usage exceeds the configured limit.
    
    Args:
        limit_gb: Memory limit in GB. If None, uses config.MEMORY_LIMIT_GB.
        fail_on_exceed: If True, raises RuntimeError when limit is exceeded.
        
    Returns:
        Dict with 'current_gb', 'limit_gb', 'exceeded' (bool), and 'message'.
        
    Raises:
        RuntimeError: If fail_on_exceed is True and limit is exceeded.
    """
    # Initialize config if not already done
    if 'config' not in sys.modules:
        initialize_config()
    
    # Get limit from config if not provided
    if limit_gb is None:
        limit_gb = get_int_config("MEMORY_LIMIT_GB", default=6)
        if isinstance(limit_gb, str):
            limit_gb = int(limit_gb)
    
    current_gb = get_memory_usage_gb()
    exceeded = current_gb > limit_gb
    
    result = {
        "current_gb": round(current_gb, 3),
        "limit_gb": limit_gb,
        "exceeded": exceeded,
        "message": f"Memory usage: {current_gb:.3f} GB / {limit_gb} GB limit"
    }
    
    if exceeded:
        result["message"] += " - EXCEEDED LIMIT"
        logger.error(result["message"])
        if fail_on_exceed:
            raise RuntimeError(
                f"Memory limit exceeded: {current_gb:.3f} GB > {limit_gb} GB. "
                f"Pipeline halted to prevent system instability."
            )
    else:
        logger.info(result["message"])
    
    return result

def force_garbage_collection() -> float:
    """
    Force garbage collection and return memory after collection.
    
    Returns:
        float: Memory usage in GB after garbage collection.
    """
    gc.collect()
    logger.info("Forced garbage collection completed.")
    return get_memory_usage_gb()

def validate_dataset_size(df, limit_gb: Optional[float] = None) -> bool:
    """
    Estimate if a DataFrame will fit within memory limits.
    
    Args:
        df: pandas DataFrame to check.
        limit_gb: Memory limit in GB.
        
    Returns:
        bool: True if DataFrame fits, False otherwise.
    """
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil not available. Skipping DataFrame size validation.")
        return True
    
    if limit_gb is None:
        limit_gb = get_int_config("MEMORY_LIMIT_GB", default=6)
        if isinstance(limit_gb, str):
            limit_gb = int(limit_gb)
    
    # Estimate DataFrame memory usage
    df_memory_gb = df.memory_usage(deep=True).sum() / (1024 ** 3)
    current_memory_gb = get_memory_usage_gb()
    projected_memory_gb = current_memory_gb + df_memory_gb
    
    if projected_memory_gb > limit_gb:
        logger.error(
            f"DataFrame size ({df_memory_gb:.3f} GB) would exceed memory limit. "
            f"Projected usage: {projected_memory_gb:.3f} GB / {limit_gb} GB"
        )
        return False
    
    logger.info(
        f"DataFrame size check passed: {df_memory_gb:.3f} GB. "
        f"Projected usage: {projected_memory_gb:.3f} GB / {limit_gb} GB"
    )
    return True

def main():
    """
    Standalone execution to demonstrate memory monitoring.
    Writes a memory status report to data/reports/memory_status.json.
    """
    import json
    
    # Ensure output directory exists
    output_dir = Path("data/reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting memory check for pipeline safety.")
    
    try:
        # Check memory limit
        status = check_memory_limit(fail_on_exceed=False)
        
        # Force GC and check again
        memory_after_gc = force_garbage_collection()
        status["memory_after_gc_gb"] = round(memory_after_gc, 3)
        
        # Write report
        report_path = output_dir / "memory_status.json"
        with open(report_path, "w") as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Memory status report written to: {report_path}")
        print(json.dumps(status, indent=2))
        
        return 0
        
    except RuntimeError as e:
        logger.error(f"Memory check failed: {e}")
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during memory check: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
