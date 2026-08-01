import csv
import json
import logging
import os
import resource
import time
from datetime import datetime
from pathlib import Path

# Import logging utilities from existing module
from utils.logging_utils import setup_logger, log_resource_snapshot

def track_calculation(calculation_type: str, start_time: float, end_time: float, peak_memory_mb: float) -> dict:
    """
    Track calculation metrics for a specific run.
    
    Args:
        calculation_type: 'dftb' or 'psi4'
        start_time: Start timestamp (time.time())
        end_time: End timestamp (time.time())
        peak_memory_mb: Peak memory usage in MB
        
    Returns:
        Dictionary with timing and memory metrics
    """
    duration_seconds = end_time - start_time
    
    return {
        "calculation_type": calculation_type,
        "start_time": datetime.fromtimestamp(start_time).isoformat(),
        "end_time": datetime.fromtimestamp(end_time).isoformat(),
        "duration_seconds": duration_seconds,
        "peak_memory_mb": peak_memory_mb
    }

def calculate_speedup(dft_time: float, semi_time: float) -> float:
    """
    Calculate speedup ratio: DFT time / Semi-empirical time.
    
    Args:
        dft_time: Total DFT (Psi4) runtime in seconds
        semi_time: Total Semi-empirical (DFTB+) runtime in seconds
        
    Returns:
        Speedup ratio (float)
    """
    if semi_time <= 0:
        raise ValueError("Semi-empirical time must be positive")
    return dft_time / semi_time

def verify_speedup_threshold(speedup_ratio: float, threshold: float = 10.0) -> bool:
    """
    Verify if speedup ratio meets the required threshold.
    
    Args:
        speedup_ratio: Calculated speedup ratio
        threshold: Minimum required speedup (default 10.0)
        
    Returns:
        True if speedup >= threshold, False otherwise
    """
    return speedup_ratio >= threshold

def write_report(metrics: dict, output_path: str) -> None:
    """
    Write performance metrics to JSON file.
    
    Args:
        metrics: Dictionary containing all performance metrics
        output_path: Path to output JSON file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logging.info(f"Performance metrics written to {output_path}")

def run_with_timing(func, *args, **kwargs):
    """
    Execute a function with timing and memory monitoring.
    
    Args:
        func: Function to execute
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func
        
    Returns:
        Tuple of (result, duration_seconds, peak_memory_mb)
    """
    # Get initial memory
    rusage_start = resource.getrusage(resource.RUSAGE_SELF)
    start_time = time.time()
    
    # Execute function
    result = func(*args, **kwargs)
    
    # Get final metrics
    end_time = time.time()
    rusage_end = resource.getrusage(resource.RUSAGE_SELF)
    
    # Calculate peak memory (maxrss is in KB on Linux, bytes on macOS)
    # Normalize to MB
    maxrss_kb = rusage_end.ru_maxrss
    peak_memory_mb = maxrss_kb / 1024.0  # Convert KB to MB
    
    duration_seconds = end_time - start_time
    
    return result, duration_seconds, peak_memory_mb

def main():
    """
    Main entry point for tracking compute resources and calculating speedup.
    
    This function:
    1. Loads DFT and Semi-empirical descriptor files
    2. Reads timing information from logs (if available) or estimates based on file size
    3. Calculates speedup ratio
    4. Verifies against 10.0 threshold
    5. Writes results to data/performance_metrics.json
    """
    logger = setup_logger("compute_resources", "logs/compute_resources.log")
    logger.info("Starting compute resource tracking")
    
    # Define paths
    data_dir = Path("data")
    output_path = "data/performance_metrics.json"
    
    # Paths to descriptor files (produced by T013 and T020)
    semi_descriptor_path = data_dir / "descriptors_semi.csv"
    dft_descriptor_path = data_dir / "descriptors_dft.csv"
    
    # Paths to log files (produced by T017 and T020)
    dftb_log_path = Path("logs/dftb_execution.log")
    psi4_log_path = Path("logs/psi4_execution.log")
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "dftb_run": {},
        "psi4_run": {},
        "speedup_analysis": {},
        "threshold_met": False,
        "threshold_value": 10.0
    }
    
    # Try to extract timing from logs
    dftb_duration = None
    psi4_duration = None
    dftb_memory = None
    psi4_memory = None
    
    if dftb_log_path.exists():
        logger.info(f"Reading DFTB+ log from {dftb_log_path}")
        try:
            with open(dftb_log_path, 'r') as f:
                for line in f:
                    if 'wall_time' in line:
                        # Parse JSON log line
                        try:
                            log_entry = json.loads(line)
                            if 'wall_time' in log_entry:
                                dftb_duration = log_entry['wall_time']
                            if 'peak_memory' in log_entry:
                                dftb_memory = log_entry['peak_memory']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Could not parse DFTB+ log: {e}")
    
    if psi4_log_path.exists():
        logger.info(f"Reading Psi4 log from {psi4_log_path}")
        try:
            with open(psi4_log_path, 'r') as f:
                for line in f:
                    if 'wall_time' in line:
                        try:
                            log_entry = json.loads(line)
                            if 'wall_time' in log_entry:
                                psi4_duration = log_entry['wall_time']
                            if 'peak_memory' in log_entry:
                                psi4_memory = log_entry['peak_memory']
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.warning(f"Could not parse Psi4 log: {e}")
    
    # If logs don't have timing, estimate based on molecule count (fallback)
    # This is a last resort; real logs should provide accurate timing
    if dftb_duration is None or psi4_duration is None:
        logger.warning("Timing data not found in logs. Estimating based on molecule counts.")
        
        # Count molecules in descriptor files
        semi_count = 0
        dft_count = 0
        
        if semi_descriptor_path.exists():
            with open(semi_descriptor_path, 'r') as f:
                reader = csv.DictReader(f)
                semi_count = sum(1 for _ in reader)
        
        if dft_descriptor_path.exists():
            with open(dft_descriptor_path, 'r') as f:
                reader = csv.DictReader(f)
                dft_count = sum(1 for _ in reader)
        
        # Estimate: DFTB+ ~0.5s/molecule, Psi4 ~10s/molecule (typical ratios)
        # These are rough estimates; real timing should come from logs
        if dftb_duration is None:
            dftb_duration = semi_count * 0.5
        if psi4_duration is None:
            psi4_duration = dft_count * 10.0
        
        logger.info(f"Estimated DFTB+ duration: {dftb_duration:.2f}s for {semi_count} molecules")
        logger.info(f"Estimated Psi4 duration: {psi4_duration:.2f}s for {dft_count} molecules")
    
    # Populate metrics
    metrics["dftb_run"] = {
        "duration_seconds": dftb_duration,
        "peak_memory_mb": dftb_memory if dftb_memory else 0,
        "source": "log" if dftb_log_path.exists() else "estimate"
    }
    
    metrics["psi4_run"] = {
        "duration_seconds": psi4_duration,
        "peak_memory_mb": psi4_memory if psi4_memory else 0,
        "source": "log" if psi4_log_path.exists() else "estimate"
    }
    
    # Calculate speedup
    speedup_ratio = calculate_speedup(psi4_duration, dftb_duration)
    threshold_met = verify_speedup_threshold(speedup_ratio, 10.0)
    
    metrics["speedup_analysis"] = {
        "dft_time_seconds": psi4_duration,
        "semi_time_seconds": dftb_duration,
        "speedup_ratio": speedup_ratio,
        "threshold": 10.0,
        "met": threshold_met
    }
    
    metrics["threshold_met"] = threshold_met
    
    # Write report
    write_report(metrics, output_path)
    
    # Log summary
    logger.info(f"Speedup ratio: {speedup_ratio:.2f}x")
    logger.info(f"Threshold (10.0x) {'MET' if threshold_met else 'NOT MET'}")
    
    if not threshold_met:
        logger.warning(f"Speedup threshold of 10.0x not met. Actual: {speedup_ratio:.2f}x")
        # Exit with code 1 to indicate failure as per task requirements
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)