import logging
import os
import sys
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

# Ensure logs directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Relative path to log file (under logs/)
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Formatter for structured logs
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = os.path.join(LOGS_DIR, log_file)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_dftb_invocation(
    logger: logging.Logger,
    molecule_id: str,
    input_file: str,
    command: str,
    working_dir: str
) -> None:
    """
    Log the start of a DFTB+ calculation invocation.
    
    Args:
        logger: Logger instance
        molecule_id: Unique identifier for the molecule
        input_file: Path to the DFTB+ input file
        command: The command line invocation string
        working_dir: Working directory for the calculation
    """
    logger.info(
        f"DFTB+ INVOCATION START | molecule_id={molecule_id} | "
        f"input_file={input_file} | working_dir={working_dir} | "
        f"command={command}"
    )

def log_psi4_invocation(
    logger: logging.Logger,
    molecule_id: str,
    input_file: str,
    command: str,
    working_dir: str
) -> None:
    """
    Log the start of a Psi4 calculation invocation.
    
    Args:
        logger: Logger instance
        molecule_id: Unique identifier for the molecule
        input_file: Path to the Psi4 input file
        command: The command line invocation string
        working_dir: Working directory for the calculation
    """
    logger.info(
        f"PSI4 INVOCATION START | molecule_id={molecule_id} | "
        f"input_file={input_file} | working_dir={working_dir} | "
        f"command={command}"
    )

def get_resource_usage() -> Dict[str, Any]:
    """
    Get current CPU and memory usage of the current process.
    
    Returns:
        Dictionary with 'cpu_time', 'rss_mb', 'vms_mb'
    """
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        'cpu_time': usage.ru_utime + usage.ru_stime,
        'rss_mb': usage.ru_maxrss / 1024.0,  # Convert KB to MB (Linux)
        'vms_mb': 0  # Not directly available via resource on all platforms
    }

def log_resource_snapshot(
    logger: logging.Logger,
    molecule_id: str,
    stage: str,
    resource_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a snapshot of resource usage at a specific stage.
    
    Args:
        logger: Logger instance
        molecule_id: Unique identifier for the molecule
        stage: Stage name (e.g., 'start', 'geometry_opt', 'done')
        resource_data: Optional pre-computed resource data
    """
    if resource_data is None:
        resource_data = get_resource_usage()
    
    logger.info(
        f"RESOURCE SNAPSHOT | molecule_id={molecule_id} | stage={stage} | "
        f"cpu_time={resource_data['cpu_time']:.2f}s | "
        f"rss_mb={resource_data['rss_mb']:.2f}MB"
    )

@contextmanager
def timed_section(
    logger: logging.Logger,
    molecule_id: str,
    section_name: str,
    log_file: Optional[str] = None
):
    """
    Context manager to time a code block and log results.
    
    Args:
        logger: Logger instance
        molecule_id: Unique identifier for the molecule
        section_name: Name of the timed section
        log_file: Optional log file for structured JSON output
    """
    start_time = time.time()
    start_cpu = time.process_time()
    
    logger.info(f"TIMED SECTION START | molecule_id={molecule_id} | section={section_name}")
    
    try:
        yield
        success = True
    except Exception as e:
        success = False
        logger.error(f"TIMED SECTION FAILED | molecule_id={molecule_id} | section={section_name} | error={str(e)}")
        raise
    finally:
        end_time = time.time()
        end_cpu = time.process_time()
        
        wall_time = end_time - start_time
        cpu_time = end_cpu - start_cpu
        
        resource_data = get_resource_usage()
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'molecule_id': molecule_id,
            'section': section_name,
            'wall_time_sec': round(wall_time, 3),
            'cpu_time_sec': round(cpu_time, 3),
            'peak_rss_mb': round(resource_data['rss_mb'], 2),
            'success': success
        }
        
        logger.info(
            f"TIMED SECTION END | molecule_id={molecule_id} | section={section_name} | "
            f"wall_time={wall_time:.3f}s | cpu_time={cpu_time:.3f}s | "
            f"peak_rss={resource_data['rss_mb']:.2f}MB"
        )
        
        # Write structured JSON log if file specified
        if log_file:
            log_path = os.path.join(LOGS_DIR, log_file)
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            
            # Append to JSON lines file
            with open(log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')

def log_calculation_summary(
    logger: logging.Logger,
    molecule_id: str,
    total_wall_time: float,
    total_cpu_time: float,
    peak_rss_mb: float,
    descriptors_extracted: bool,
    output_file: Optional[str] = None
) -> None:
    """
    Log a summary of the entire calculation for a molecule.
    
    Args:
        logger: Logger instance
        molecule_id: Unique identifier for the molecule
        total_wall_time: Total wall clock time in seconds
        total_cpu_time: Total CPU time in seconds
        peak_rss_mb: Peak memory usage in MB
        descriptors_extracted: Whether descriptors were successfully extracted
        output_file: Optional path to structured log file
    """
    summary = {
        'molecule_id': molecule_id,
        'total_wall_time_sec': round(total_wall_time, 3),
        'total_cpu_time_sec': round(total_cpu_time, 3),
        'peak_rss_mb': round(peak_rss_mb, 2),
        'descriptors_extracted': descriptors_extracted,
        'status': 'SUCCESS' if descriptors_extracted else 'FAILED'
    }
    
    logger.info(
        f"CALCULATION SUMMARY | molecule_id={molecule_id} | "
        f"wall_time={total_wall_time:.3f}s | cpu_time={total_cpu_time:.3f}s | "
        f"peak_rss={peak_rss_mb:.2f}MB | status={'SUCCESS' if descriptors_extracted else 'FAILED'}"
    )
    
    if output_file:
        log_path = os.path.join(LOGS_DIR, output_file)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(summary) + '\n')

def main():
    """Demo of logging utilities."""
    logger = setup_logger(__name__, 'test_dftb_execution.log')
    
    with timed_section(logger, 'MOL-001', 'geometry_optimization', 'dftb_execution.log'):
        time.sleep(0.1)
        logger.info("Simulating DFTB+ calculation...")
    
    log_resource_snapshot(logger, 'MOL-001', 'end')

if __name__ == '__main__':
    main()