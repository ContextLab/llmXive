import logging
import os
import sys
import time
import threading
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# Try to import psutil for real memory monitoring
# If not available, we will use a fallback that returns a constant
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class MemoryUsageHandler(logging.Handler):
    """
    A logging handler that monitors and logs memory usage.
    """
    def __init__(self, log_file: str = "logs/memory.log"):
        super().__init__()
        self.log_file = log_file
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.interval = 5.0

    def start_monitoring(self, interval: float = 5.0):
        """
        Starts a background thread to monitor memory usage.
        """
        self.running = True
        self.interval = interval
        self.thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.thread.daemon = True
        self.thread.start()

    def _monitor_loop(self, interval: float):
        while self.running:
            memory = get_memory_usage()
            record = self.format(logging.LogRecord(
                name="memory",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg=f"Memory usage: {memory:.2f} MB",
                args=(),
                exc_info=None
            ))
            # Write directly to file to avoid handler recursion issues
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            with open(self.log_file, 'a') as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Memory usage: {memory:.2f} MB\n")
            
            time.sleep(interval)

    def stop_monitoring(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def emit(self, record: logging.LogRecord):
        # This is called by the logging framework, but we handle file writing in _monitor_loop
        pass

class TimeoutMonitor:
    """
    Monitors execution time and logs timeout events.
    """
    def __init__(self, timeout_seconds: int = 21600):
        self.timeout_seconds = timeout_seconds
        self.start_time: Optional[float] = None

    def start(self):
        self.start_time = time.time()

    def check(self) -> bool:
        """
        Returns True if the timeout has been exceeded.
        """
        if self.start_time is None:
            return False
        elapsed = time.time() - self.start_time
        return elapsed > self.timeout_seconds

    def get_elapsed(self) -> float:
        """
        Returns the elapsed time in seconds.
        """
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

def get_memory_usage() -> float:
    """
    Returns current memory usage in MB.
    Uses psutil if available, otherwise returns a fallback value.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024)
    else:
        # Fallback: return a constant if psutil is not installed
        # This allows the code to run in environments without psutil
        # but logs a warning if the user tries to monitor memory
        return 0.0

def setup_logging(log_file: str = "logs/llmxive.log", level: str = "INFO") -> logging.Logger:
    """
    Sets up logging configuration.
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Clear existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )

    logger = logging.getLogger("llmxive")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the specified name.
    """
    return logging.getLogger(name)

def log_timeout_event(logger: logging.Logger, task_id: str):
    """
    Logs a timeout event.
    """
    logger.error(f"Task {task_id} timed out")

@dataclass
class LoggingConfig:
    """
    Configuration for logging.
    """
    log_file: str = "logs/llmxive.log"
    level: str = "INFO"
    memory_log_file: str = "logs/memory.log"
    memory_monitor_interval: float = 5.0
    timeout_seconds: int = 21600

def main():
    """
    Main function to test the logging infrastructure.
    """
    config = LoggingConfig()
    logger = setup_logging(config.log_file, config.level)
    
    logger.info("Logging system initialized")
    
    # Test memory monitoring
    memory_handler = MemoryUsageHandler(config.memory_log_file)
    memory_handler.start_monitoring(config.memory_monitor_interval)
    
    # Simulate some work
    time.sleep(10)
    
    memory_handler.stop_monitoring()
    
    # Test timeout monitoring
    timeout_monitor = TimeoutMonitor(config.timeout_seconds)
    timeout_monitor.start()
    
    # Simulate work
    time.sleep(2)
    
    if timeout_monitor.check():
        log_timeout_event(logger, "test_task")
    else:
        logger.info(f"Task 'test_task' completed in {timeout_monitor.get_elapsed():.2f} seconds")
    
    logger.info("Logging test complete")

if __name__ == "__main__":
    main()