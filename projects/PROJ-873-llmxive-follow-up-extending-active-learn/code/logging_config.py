import logging
import json
import os
import sys
import time
import threading
import resource
from typing import Optional, Dict, Any, List

# Global variables for logging
comparison_log_file: Optional[str] = None
resource_log_file: Optional[str] = None
resource_monitor_thread: Optional[threading.Thread] = None
stop_monitoring_event: Optional[threading.Event] = None
_logger: Optional[logging.Logger] = None

# Ensure the root logger is configured early
def _ensure_root_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
        # If root hasn't been configured yet, configure it to avoid errors
        if not logging.root.handlers:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(sys.stdout),
                    logging.FileHandler('data/logs/pipeline.log')
                ]
            )
    return _logger

def init_logging(log_dir: str = 'data/logs'):
    """Initialize logging infrastructure."""
    os.makedirs(log_dir, exist_ok=True)
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    
    global comparison_log_file, resource_log_file
    comparison_log_file = os.path.join(log_dir, f'comparisons_{timestamp}.jsonl')
    resource_log_file = os.path.join(log_dir, f'resources_{timestamp}.jsonl')
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(log_dir, f'pipeline_{timestamp}.log'))
        ]
    )
    
    logger = _ensure_root_logger()
    logger.info("Logging initialized")
    return comparison_log_file, resource_log_file

def log_pairwise_comparison(pair_data: Dict[str, Any]):
    """Log a pairwise comparison to the JSONL file."""
    if comparison_log_file:
        with open(comparison_log_file, 'a') as f:
            f.write(json.dumps(pair_data) + '\n')

def _monitor_resources(interval: float = 1.0):
    """Monitor resource usage in a background thread."""
    global stop_monitoring_event
    stop_monitoring_event = threading.Event()
    
    logger = _ensure_root_logger()
    
    while not stop_monitoring_event.is_set():
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, MB on macOS
        if sys.platform == 'darwin':
            memory_mb = usage.ru_maxrss
        else:
            memory_mb = usage.ru_maxrss / 1024
        
        log_entry = {
            'timestamp': time.time(),
            'cpu_time_user': usage.ru_utime,
            'cpu_time_system': usage.ru_stime,
            'max_memory_mb': memory_mb
        }
        
        if resource_log_file:
            with open(resource_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        
        time.sleep(interval)

def start_resource_monitoring(interval: float = 1.0):
    """Start resource monitoring in a background thread."""
    global resource_monitor_thread
    resource_monitor_thread = threading.Thread(target=_monitor_resources, args=(interval,), daemon=True)
    resource_monitor_thread.start()
    _ensure_root_logger().info("Resource monitoring started")

def stop_resource_monitoring():
    """Stop resource monitoring."""
    global stop_monitoring_event, resource_monitor_thread
    if stop_monitoring_event:
        stop_monitoring_event.set()
    if resource_monitor_thread:
        resource_monitor_thread.join(timeout=2.0)
        resource_monitor_thread = None
    _ensure_root_logger().info("Resource monitoring stopped")

def get_comparison_log_path() -> Optional[str]:
    """Get the path to the comparison log file."""
    return comparison_log_file

def get_resource_log_path() -> Optional[str]:
    """Get the path to the resource log file."""
    return resource_log_file

def main():
    """Main function for testing logging configuration."""
    init_logging()
    log_pairwise_comparison({'test': 'data', 'timestamp': time.time()})
    start_resource_monitoring(interval=0.5)
    time.sleep(2)
    stop_resource_monitoring()
    print(f"Comparison log: {get_comparison_log_path()}")
    print(f"Resource log: {get_resource_log_path()}")

if __name__ == '__main__':
    main()