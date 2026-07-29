"""
Runtime and memory tracking for DFTB+ and Psi4 calculations.

This module implements logging for computational resource usage (time and memory)
for both semi-empirical (DFTB+) and high-level DFT (Psi4) calculations. It calculates
the speedup ratio (DFT time / Semi-empirical time) and verifies against the 10x threshold
defined in SC-004.

Usage:
    Call `track_calculation()` around the execution of DFTB+ or Psi4 subprocesses.
    Results are logged and optionally written to a CSV report.
"""
import csv
import logging
import os
import resource
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Import existing utilities
from utils.logging_utils import setup_logger, log_resource_snapshot
from utils.memory_monitor import get_current_process_rss_bytes

# Constants
SPEEDUP_THRESHOLD = 10.0
LOG_FILE = "data/compute_resources.log"
REPORT_FILE = "data/compute_resources_report.csv"

logger = setup_logger("compute_tracking", LOG_FILE)


def track_calculation(
    method: str,
    molecule_id: str,
    start_time: float,
    end_time: float,
    peak_memory_bytes: int,
    success: bool = True,
    error_msg: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a single calculation's resource usage.
    
    Args:
        method: 'dftb' or 'psi4'
        molecule_id: Unique identifier for the molecule
        start_time: Start timestamp (float)
        end_time: End timestamp (float)
        peak_memory_bytes: Peak RSS memory in bytes
        success: Whether the calculation succeeded
        error_msg: Optional error message if failed
        
    Returns:
        Dictionary with recorded metrics
    """
    duration_seconds = end_time - start_time
    peak_memory_mb = peak_memory_bytes / (1024 * 1024)
    
    record = {
        "timestamp": datetime.now().isoformat(),
        "molecule_id": molecule_id,
        "method": method,
        "duration_seconds": duration_seconds,
        "peak_memory_mb": peak_memory_mb,
        "success": success,
        "error_msg": error_msg
    }
    
    log_resource_snapshot(
        logger,
        method=method,
        molecule_id=molecule_id,
        duration=duration_seconds,
        memory_mb=peak_memory_mb,
        success=success
    )
    
    return record


def calculate_speedup(dft_records: List[Dict], semi_records: List[Dict]) -> Optional[float]:
    """
    Calculate the speedup ratio: DFT time / Semi-empirical time.
    
    Uses median times to be robust against outliers.
    
    Args:
        dft_records: List of successful DFT (Psi4) calculation records
        semi_records: List of successful semi-empirical (DFTB+) calculation records
        
    Returns:
        Speedup ratio (float) or None if insufficient data
    """
    if not dft_records or not semi_records:
        logger.warning("Insufficient data to calculate speedup ratio")
        return None
        
    dft_times = [r["duration_seconds"] for r in dft_records if r["success"]]
    semi_times = [r["duration_seconds"] for r in semi_records if r["success"]]
    
    if not dft_times or not semi_times:
        logger.warning("No successful calculations found for speedup calculation")
        return None
        
    import statistics
    median_dft = statistics.median(dft_times)
    median_semi = statistics.median(semi_times)
    
    if median_semi <= 0:
        logger.error("Semi-empirical median time is zero or negative, cannot compute speedup")
        return None
        
    speedup = median_dft / median_semi
    logger.info(f"Speedup ratio (DFT/Semi): {speedup:.2f}x (DFT: {median_dft:.2f}s, Semi: {median_semi:.2f}s)")
    return speedup


def verify_speedup_threshold(speedup: Optional[float]) -> bool:
    """
    Verify if the speedup meets the 10x threshold (SC-004).
    
    Args:
        speedup: Calculated speedup ratio
        
    Returns:
        True if speedup >= 10.0, False otherwise
    """
    if speedup is None:
        logger.error("Cannot verify threshold: speedup ratio is None")
        return False
        
    if speedup >= SPEEDUP_THRESHOLD:
        logger.info(f"✓ Speedup threshold MET: {speedup:.2f}x >= {SPEEDUP_THRESHOLD}x")
        return True
    else:
        logger.error(f"✗ Speedup threshold FAILED: {speedup:.2f}x < {SPEEDUP_THRESHOLD}x")
        return False


def write_report(records: List[Dict], output_path: str) -> None:
    """
    Write calculation records to a CSV report.
    
    Args:
        records: List of calculation record dictionaries
        output_path: Path to output CSV file
    """
    if not records:
        logger.warning("No records to write")
        return
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ["timestamp", "molecule_id", "method", "duration_seconds", 
                 "peak_memory_mb", "success", "error_msg"]
                 
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
        
    logger.info(f"Report written to {output_path}")


def run_with_timing(
    func,
    method: str,
    molecule_id: str,
    *args,
    **kwargs
) -> tuple:
    """
    Decorator-like function to run a calculation with automatic timing and memory tracking.
    
    Args:
        func: The calculation function to run
        method: 'dftb' or 'psi4'
        molecule_id: Molecule identifier
        *args, **kwargs: Arguments to pass to func
        
    Returns:
        Tuple of (result, record_dict)
    """
    start_time = time.time()
    peak_memory = get_current_process_rss_bytes()
    success = True
    error_msg = None
    result = None
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"Calculation failed for {molecule_id} ({method}): {error_msg}")
        raise
    finally:
        end_time = time.time()
        current_memory = get_current_process_rss_bytes()
        peak_memory = max(peak_memory, current_memory)
        
    record = track_calculation(
        method=method,
        molecule_id=molecule_id,
        start_time=start_time,
        end_time=end_time,
        peak_memory_bytes=peak_memory,
        success=success,
        error_msg=error_msg
    )
    
    return result, record


def main():
    """
    Main entry point for resource tracking demonstration.
    
    This function is intended to be called by the descriptor generation scripts
    to wrap their execution with timing and memory monitoring.
    """
    logger.info("Compute resource tracking module initialized")
    logger.info(f"Speedup threshold: {SPEEDUP_THRESHOLD}x (SC-004)")
    
    # Example usage would be integrated into generate_descriptors.py
    # This is a placeholder for the actual integration point
    logger.info("Integration: Wrap DFTB+ and Psi4 calls with run_with_timing()")


if __name__ == "__main__":
    main()
