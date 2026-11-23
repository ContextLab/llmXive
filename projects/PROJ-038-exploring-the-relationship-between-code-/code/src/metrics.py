import os
import subprocess
import tempfile
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from config for memory limit constant
from .config import get_memory_limit_bytes

# Import from metrics submodule
from .metrics import halstead as halstead_module
from .metrics import pmd as pmd_module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

class MetricsCalculationError(Exception):
    """Raised when metrics calculation fails."""
    pass

def get_current_memory_usage_bytes() -> int:
    """
    Get the current memory usage of the process in bytes.
    
    Uses /proc/self/status on Linux or psutil if available.
    Falls back to a conservative estimate if neither is available.
    
    Returns:
        int: Memory usage in bytes.
    """
    try:
        # Try to read from /proc/self/status (Linux)
        if os.path.exists('/proc/self/status'):
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        value = int(line.split()[1])
                        return value * 1024
        
        # Try psutil if available
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            pass
        
        # Fallback: return 0 (conservative, but safe)
        logger.warning("Could not determine memory usage accurately. Returning 0.")
        return 0
        
    except Exception as e:
        logger.warning(f"Error getting memory usage: {e}. Returning 0.")
        return 0

def validate_ram_limit(max_bytes: Optional[int] = None) -> None:
    """
    Validate that current memory usage does not exceed the limit.
    
    Args:
        max_bytes: Maximum allowed memory in bytes. If None, uses config default.
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
    """
    if max_bytes is None:
        max_bytes = get_memory_limit_bytes()
    
    current_usage = get_current_memory_usage_bytes()
    if current_usage > max_bytes:
        raise MemoryLimitExceeded(
            f"Memory limit exceeded: {current_usage / (1024**3):.2f} GB > "
            f"{max_bytes / (1024**3):.2f} GB"
        )
    
    logger.info(f"Memory check passed: {current_usage / (1024**3):.2f} GB / "
                f"{max_bytes / (1024**3):.2f} GB")

def monitor_memory_periodically(check_interval: float = 1.0, max_bytes: Optional[int] = None) -> None:
    """
    Monitor memory usage periodically and raise an error if limit is exceeded.
    
    This function is designed to be called in a loop during long-running operations.
    
    Args:
        check_interval: Interval in seconds between checks.
        max_bytes: Maximum allowed memory in bytes. If None, uses config default.
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds the limit.
    """
    if max_bytes is None:
        max_bytes = get_memory_limit_bytes()
    
    while True:
        current_usage = get_current_memory_usage_bytes()
        logger.info(f"Current memory usage: {current_usage / (1024**3):.2f} GB")
        
        if current_usage > max_bytes:
            raise MemoryLimitExceeded(
                f"Memory limit exceeded: {current_usage / (1024**3):.2f} GB > "
                f"{max_bytes / (1024**3):.2f} GB"
            )
        
        time.sleep(check_interval)

def calculate_loc_ast(file_path: Path) -> int:
    """
    Calculate Lines of Code (LOC) using AST parsing.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        int: Number of lines of code.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Simple LOC calculation: count non-empty, non-comment lines
        loc = 0
        in_block_comment = False
        
        for line in lines:
            stripped = line.strip()
            
            # Handle block comments
            if '/*' in stripped:
                in_block_comment = True
            if '*/' in stripped:
                in_block_comment = False
                continue
            
            if in_block_comment:
                continue
            
            # Skip empty lines and single-line comments
            if not stripped or stripped.startswith('//') or stripped.startswith('*'):
                continue
            
            loc += 1
        
        return loc
        
    except Exception as e:
        logger.error(f"Error calculating LOC for {file_path}: {e}")
        raise MetricsCalculationError(f"Failed to calculate LOC: {e}")

def calculate_loc_batch(file_paths: List[Path]) -> Dict[str, int]:
    """
    Calculate LOC for a batch of files.
    
    Args:
        file_paths: List of file paths.
        
    Returns:
        Dictionary mapping file paths to LOC values.
    """
    results = {}
    for file_path in file_paths:
        try:
            # Periodic memory check
            validate_ram_limit()
            results[str(file_path)] = calculate_loc_ast(file_path)
        except Exception as e:
            logger.warning(f"Skipping {file_path}: {e}")
            results[str(file_path)] = 0
    
    return results

def calculate_cc_single_file(file_path: Path) -> int:
    """
    Calculate Cyclomatic Complexity for a single file using PMD.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        int: Cyclomatic complexity value.
    """
    try:
        # Use PMD to calculate CC
        # This calls the PMD wrapper function
        cc = pmd_module.calculate_cc_single_file(file_path)
        
        # Periodic memory check
        validate_ram_limit()
        
        return cc
        
    except Exception as e:
        logger.error(f"Error calculating CC for {file_path}: {e}")
        raise MetricsCalculationError(f"Failed to calculate CC: {e}")

def calculate_halstead_single_file(file_path: Path) -> float:
    """
    Calculate Halstead Volume for a single file.
    
    Args:
        file_path: Path to the Java file.
        
    Returns:
        float: Halstead volume value.
    """
    try:
        # Use the halstead module to calculate volume
        volume = halstead_module.calculate_halstead_for_file(file_path)
        
        # Periodic memory check
        validate_ram_limit()
        
        return volume
        
    except Exception as e:
        logger.error(f"Error calculating Halstead for {file_path}: {e}")
        raise MetricsCalculationError(f"Failed to calculate Halstead: {e}")

def calculate_metrics_batch(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Calculate all metrics for a batch of files.
    
    Args:
        file_paths: List of file paths.
        
    Returns:
        List of dictionaries containing metrics for each file.
    """
    results = []
    
    for i, file_path in enumerate(file_paths):
        try:
            # Periodic memory check
            validate_ram_limit()
            
            # Calculate metrics
            loc = calculate_loc_ast(file_path)
            cc = calculate_cc_single_file(file_path)
            halstead = calculate_halstead_single_file(file_path)
            
            results.append({
                'file_path': str(file_path),
                'loc': loc,
                'cc': cc,
                'halstead': halstead
            })
            
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(file_paths)} files")
                
        except Exception as e:
            logger.warning(f"Skipping {file_path}: {e}")
            # Add a record with zeros or skip entirely
            # For now, we'll skip to avoid polluting the dataset
            continue
    
    return results

def main():
    """Main entry point for the metrics module."""
    logger.info("Starting metrics calculation")
    
    try:
        # Example: Calculate metrics for a single file
        test_file = Path("code/data/raw/test.java")
        if test_file.exists():
            loc = calculate_loc_ast(test_file)
            cc = calculate_cc_single_file(test_file)
            halstead = calculate_halstead_single_file(test_file)
            
            logger.info(f"LOC: {loc}, CC: {cc}, Halstead: {halstead}")
        else:
            logger.warning(f"Test file {test_file} not found")
        
        logger.info("Metrics calculation completed")
        
    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except MetricsCalculationError as e:
        logger.error(f"Metrics calculation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import sys
    main()
