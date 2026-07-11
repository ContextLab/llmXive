import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

import psutil

from utils.logger import get_logger
from utils.config import get_project_root, get_output_path

# Configuration
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours
MEMORY_THRESHOLD_GB = 7.0

logger = get_logger(__name__)

def get_process_memory_gb() -> float:
    """Return current process memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_memory_threshold() -> bool:
    """Check if current memory usage exceeds threshold."""
    current_gb = get_process_memory_gb()
    if current_gb > MEMORY_THRESHOLD_GB:
        logger.warning(f"Memory usage {current_gb:.2f}GB exceeds threshold {MEMORY_THRESHOLD_GB}GB")
        return False
    return True

@contextmanager
def performance_timer(operation_name: str):
    """Context manager to time an operation and log results."""
    start_time = time.time()
    logger.info(f"Starting operation: {operation_name}")
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(f"Completed operation: {operation_name} in {duration:.2f} seconds")
        
        # Check total runtime
        if duration > MAX_RUNTIME_SECONDS:
            logger.error(f"Operation {operation_name} exceeded max runtime limit")
            raise TimeoutError(f"Operation {operation_name} exceeded {MAX_RUNTIME_SECONDS} seconds")

def optimize_data_loading(df) -> None:
    """Optimize DataFrame memory usage by downcasting numeric types."""
    import pandas as pd
    
    initial_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)
    
    for col in df.columns:
        col_type = df[col].dtype
        
        if pd.api.types.is_integer_dtype(col_type):
            col_min = df[col].min()
            col_max = df[col].max()
            
            if pd.api.types.is_signed_integer_dtype(col_type):
                if col_min >= 0:
                    if col_max <= 255:
                        df[col] = pd.to_numeric(df[col], downcast='unsigned')
                    elif col_max <= 65535:
                        df[col] = pd.to_numeric(df[col], downcast='unsigned')
                else:
                    if col_min >= -128 and col_max <= 127:
                        df[col] = pd.to_numeric(df[col], downcast='integer')
                    elif col_min >= -32768 and col_max <= 32767:
                        df[col] = pd.to_numeric(df[col], downcast='integer')
            elif pd.api.types.is_unsigned_integer_dtype(col_type):
                if col_max <= 255:
                    df[col] = pd.to_numeric(df[col], downcast='unsigned')
                elif col_max <= 65535:
                    df[col] = pd.to_numeric(df[col], downcast='unsigned')
                
        elif pd.api.types.is_float_dtype(col_type):
            col_min = df[col].min()
            col_max = df[col].max()
            if col_min >= 0 and col_max <= 1:
                df[col] = pd.to_numeric(df[col], downcast='float')
            else:
                if col_min >= -3.4e38 and col_max <= 3.4e38:
                    df[col] = pd.to_numeric(df[col], downcast='float')
        
        if pd.api.types.is_object_dtype(col_type) and df[col].dtype.name == 'object':
            if df[col].nunique() / len(df) < 0.5:
                df[col] = df[col].astype('category')
    
    optimized_memory = df.memory_usage(deep=True).sum() / (1024 ** 2)
    reduction = ((initial_memory - optimized_memory) / initial_memory) * 100
    logger.info(f"Memory optimization: {initial_memory:.2f}MB -> {optimized_memory:.2f}MB ({reduction:.1f}% reduction)")

def save_performance_report(report_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Save performance metrics to a JSON file."""
    if output_path is None:
        output_dir = get_output_path()
        output_path = str(Path(output_dir) / "performance_report.json")
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Performance report saved to {output_path}")
    return output_path

def run_performance_optimization() -> Dict[str, Any]:
    """
    Main function to run performance optimization checks and optimizations.
    Returns a dictionary with performance metrics.
    """
    logger.info("Starting performance optimization check")
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "max_runtime_seconds": MAX_RUNTIME_SECONDS,
        "memory_threshold_gb": MEMORY_THRESHOLD_GB,
        "checks": []
    }
    
    # Check 1: Memory usage
    mem_gb = get_process_memory_gb()
    mem_check = {
        "check_name": "memory_usage",
        "current_gb": mem_gb,
        "threshold_gb": MEMORY_THRESHOLD_GB,
        "passed": mem_gb <= MEMORY_THRESHOLD_GB,
        "message": f"Memory usage: {mem_gb:.2f}GB"
    }
    report["checks"].append(mem_check)
    
    if not mem_check["passed"]:
        logger.warning(mem_check["message"])
    
    # Check 2: Runtime budget
    # This is a static check since we don't have a running process context here
    runtime_check = {
        "check_name": "runtime_budget",
        "max_seconds": MAX_RUNTIME_SECONDS,
        "passed": True,
        "message": f"Runtime budget set to {MAX_RUNTIME_SECONDS} seconds (6 hours)"
    }
    report["checks"].append(runtime_check)
    
    # Save report
    report_path = save_performance_report(report)
    report["report_path"] = report_path
    
    logger.info("Performance optimization check completed")
    return report

def main():
    """Entry point for performance optimization script."""
    parser = argparse.ArgumentParser(description="Run performance optimization checks")
    parser.add_argument("--output", type=str, help="Output path for performance report", default=None)
    args = parser.parse_args()
    
    try:
        report = run_performance_optimization()
        
        # Check if any critical checks failed
        critical_failures = [c for c in report["checks"] if not c["passed"] and c["check_name"] == "memory_usage"]
        
        if critical_failures:
            logger.error("Critical performance thresholds exceeded")
            sys.exit(1)
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Performance optimization failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
