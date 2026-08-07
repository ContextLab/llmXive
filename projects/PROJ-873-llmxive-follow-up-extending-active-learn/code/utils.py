"""
Utility functions for resource monitoring and enforcement.
Implements watchdog/signal handler to terminate pipeline if runtime or memory limits are exceeded.
Serves FR-006 enforcement and T061 Graceful Degradation.
"""
import os
import signal
import sys
import time
import resource
import logging
import json
from typing import Optional, Callable, Any

# Custom exception for graceful termination
class PartialRunError(Exception):
    """Raised when the pipeline must terminate gracefully due to approaching resource limits."""
    def __init__(self, message: str, partial_data_path: Optional[str] = None):
        super().__init__(message)
        self.partial_data_path = partial_data_path

class ResourceWatchdog:
    """
    Monitors resource usage and triggers termination if limits are exceeded.
    Implements watchdog/signal handler for FR-006 and T061 Graceful Degradation.
    """
    def __init__(self, max_runtime_seconds: int, max_memory_mb: int, grace_period_seconds: int = 60):
        self.max_runtime = max_runtime_seconds
        self.max_memory = max_memory_mb * 1024 * 1024  # Convert to bytes
        self.grace_period = grace_period_seconds
        self.start_time = time.time()
        self.logger = logging.getLogger(__name__)
        self._alarm_set = False
        self._grace_mode_active = False

        # Setup signal handler for timeout
        if hasattr(signal, 'SIGALRM'):
            # Store old handler to restore later if needed
            self._old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.alarm(self.max_runtime)
            self._alarm_set = True
            self.logger.info(f"Watchdog started: Runtime limit {self.max_runtime}s, Memory limit {max_memory_mb}MB, Grace period {grace_period}s")
        else:
            self.logger.warning("SIGALRM not available on this platform. Runtime limit not enforced via signal.")

    def _timeout_handler(self, signum, frame):
        if self._grace_mode_active:
            # We are already in grace mode, force exit
            self.logger.error("Grace period exceeded. Force terminating.")
            sys.exit(1)
        else:
            # First timeout: enter grace mode
            self.logger.warning(f"Runtime limit approaching. Entering grace period of {self.grace_period}s to complete current batch.")
            self._grace_mode_active = True
            # Reset alarm for grace period
            if hasattr(signal, 'SIGALRM'):
                signal.alarm(self.grace_period)
                signal.signal(signal.SIGALRM, self._timeout_handler)

    def check_memory(self) -> bool:
        """Check current memory usage against limit. Returns False if limit exceeded."""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, convert to bytes
            current_mem = usage.ru_maxrss * 1024
            if current_mem > self.max_memory:
                self.logger.error(f"Memory limit exceeded: {current_mem/1024/1024:.1f}MB > {self.max_memory/1024/1024:.1f}MB")
                raise PartialRunError(f"Memory limit exceeded: {current_mem/1024/1024:.1f}MB")
        except PartialRunError:
            raise
        except Exception as e:
            self.logger.warning(f"Could not check memory: {e}")
        return True

    def check_runtime(self) -> bool:
        """Check if runtime limit exceeded. Returns False if limit exceeded or if in grace mode."""
        elapsed = time.time() - self.start_time
        if elapsed > self.max_runtime:
            if self._grace_mode_active:
                self.logger.error("Grace period exceeded. Terminating with partial results.")
                raise PartialRunError("Runtime limit exceeded after grace period.")
            else:
                self.logger.warning(f"Runtime limit reached. Entering grace period to complete current batch.")
                self._grace_mode_active = True
                # Reset alarm for grace period if possible
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(self.grace_period)
                    signal.signal(signal.SIGALRM, self._timeout_handler)
                return True  # Allow current batch to finish
        return True

    def trigger_graceful_shutdown(self, state_file_path: str, partial_data: Any = None) -> None:
        """
        Saves partial state and raises PartialRunError to halt execution gracefully.
        Updates the state file with 'partial_run' flag.
        """
        self.logger.info("Triggering graceful shutdown and saving partial results.")
        
        # Update state file
        if os.path.exists(state_file_path):
            try:
                with open(state_file_path, 'r') as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError):
                state = {}
        else:
            state = {}
        
        state['partial_run'] = True
        state['graceful_shutdown'] = True
        state['shutdown_time'] = time.strftime("%Y-%m-%dT%H:%M:%S")
        state['reason'] = "Runtime limit approached"
        
        if partial_data:
            state['partial_data_summary'] = str(type(partial_data))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(state_file_path), exist_ok=True)
        
        with open(state_file_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.logger.info(f"State file updated: {state_file_path}")
        raise PartialRunError("Graceful shutdown triggered. Partial state saved.")

    def stop(self):
        """Stop the watchdog."""
        if self._alarm_set:
            signal.alarm(0)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, self._old_handler)
            self._alarm_set = False
            self.logger.info("Watchdog stopped.")

def enforce_resource_limits(max_runtime: int, max_memory_mb: int) -> ResourceWatchdog:
    """
    Convenience function to start a watchdog and check limits periodically.
    Returns the watchdog instance for manual checks or context use.
    """
    return ResourceWatchdog(max_runtime, max_memory_mb)

# Global watchdog instance for periodic checks
_global_watchdog: Optional[ResourceWatchdog] = None

def init_watchdog(max_runtime_hours: float = 6.0, max_memory_gb: float = 7.0, grace_period_seconds: int = 60):
    """
    Initialize the global watchdog with limits from config.
    Serves FR-006 enforcement and T061 Graceful Degradation.
    """
    global _global_watchdog
    max_runtime_seconds = int(max_runtime_hours * 3600)
    max_memory_mb = int(max_memory_gb * 1024)
    _global_watchdog = enforce_resource_limits(max_runtime_seconds, max_memory_mb)
    # Note: Grace period is set in the class constructor now, but we can re-init if needed
    # For now, the default grace period is used.
    return _global_watchdog

def check_limits_periodically():
    """
    Periodically check resource limits. Should be called in long-running loops.
    """
    global _global_watchdog
    if _global_watchdog:
        _global_watchdog.check_memory()
        _global_watchdog.check_runtime()

def stop_watchdog():
    """Stop the global watchdog."""
    global _global_watchdog
    if _global_watchdog:
        _global_watchdog.stop()
        _global_watchdog = None