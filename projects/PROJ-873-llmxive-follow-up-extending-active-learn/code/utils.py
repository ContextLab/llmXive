import os
import signal
import sys
import time
import resource
from threading import Timer
from config import get_config

class ResourceWatchdog:
    """
    Monitors runtime and memory usage, terminating the process if limits are exceeded.
    """
    def __init__(self, timeout_seconds: int, memory_limit_bytes: int):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_bytes = memory_limit_bytes
        self.start_time = time.time()
        self.timer = None

    def _check_memory(self):
        """Checks if memory usage exceeds the limit."""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, MB on macOS. 
            # We'll assume KB for Linux and convert, but add a check if needed.
            # For portability, we assume KB (Linux default) and convert to bytes.
            current_memory_kb = usage.ru_maxrss
            current_memory_bytes = current_memory_kb * 1024
            
            if current_memory_bytes > self.memory_limit_bytes:
                print(f"FATAL: Memory limit exceeded ({current_memory_bytes} > {self.memory_limit_bytes})", file=sys.stderr)
                os._exit(1)
        except Exception as e:
            print(f"Warning: Could not check memory: {e}", file=sys.stderr)

    def _check_time(self):
        """Checks if runtime exceeds the limit."""
        elapsed = time.time() - self.start_time
        if elapsed > self.timeout_seconds:
            print(f"FATAL: Runtime limit exceeded ({elapsed:.2f}s > {self.timeout_seconds}s)", file=sys.stderr)
            os._exit(1)

    def start(self, interval: int = 10):
        """Starts the watchdog timer."""
        def loop():
            self._check_time()
            self._check_memory()
            self.timer = Timer(interval, loop)
            self.timer.daemon = True
            self.timer.start()

        self.timer = Timer(interval, loop)
        self.timer.daemon = True
        self.timer.start()

    def stop(self):
        """Stops the watchdog timer."""
        if self.timer:
            self.timer.cancel()

def enforce_resource_limits():
    """
    Initializes and starts the resource watchdog based on config.
    """
    config = get_config()
    watchdog = ResourceWatchdog(config.runtime_limit_seconds, config.memory_limit_bytes)
    watchdog.start()
    return watchdog
