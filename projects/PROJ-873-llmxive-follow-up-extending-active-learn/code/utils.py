import os
import signal
import sys
import time
import resource
import logging
import json
from typing import Optional

from config import get_config, PipelineConfig

logger = logging.getLogger(__name__)

class PartialRunError(Exception):
    pass

class DataFlowViolationError(Exception):
    pass

class ResourceWatchdog:
    def __init__(self, max_runtime_hours: float, max_memory_gb: float):
        self.max_runtime_hours = max_runtime_hours
        self.max_memory_gb = max_memory_gb
        self.start_time = time.time()
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.running = True

    def check(self):
        if not self.running:
            return

        elapsed = time.time() - self.start_time
        elapsed_hours = elapsed / 3600

        if elapsed_hours > self.max_runtime_hours:
            logger.error(f"Runtime limit exceeded: {elapsed_hours:.2f}h > {self.max_runtime_hours}h")
            self._hard_kill()

        try:
            mem_usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB; on macOS, it might be bytes.
            # Assuming Linux for consistency with cgroups context
            mem_gb = mem_usage / (1024 * 1024) 
            if mem_gb > self.max_memory_gb:
                logger.error(f"Memory limit exceeded: {mem_gb:.2f}GB > {self.max_memory_gb}GB")
                self._hard_kill()
        except Exception as e:
            logger.warning(f"Could not check memory: {e}")

    def _hard_kill(self):
        logger.critical("Initiating hard kill.")
        os.kill(os.getpid(), signal.SIGKILL)

    def stop(self):
        self.running = False

def init_watchdog():
    config = get_config()
    watchdog = ResourceWatchdog(
        max_runtime_hours=config.MAX_RUNTIME_HOURS,
        max_memory_gb=config.MAX_MEMORY_GB
    )
    
    # T004a: Dual-Layer Hard Kill
    # Layer 1: psutil signals (handled in check via os.kill)
    # Layer 2: Shell wrapper (handled by external script or cgroups if available)
    
    # Verify cgroups or psutil availability
    try:
        # Check if cgroups v2 are available
        with open('/sys/fs/cgroup/cgroup.controllers', 'r') as f:
            pass
        logger.info("cgroups v2 available.")
    except FileNotFoundError:
        logger.warning("cgroups v2 not available. Fallback to psutil/ulimit.")
        # Fallback logic handled by watchdog check loop
    
    return watchdog

def check_limits_periodically(watchdog: ResourceWatchdog, interval: int = 60):
    while watchdog.running:
        watchdog.check()
        time.sleep(interval)

def stop_watchdog(watchdog: ResourceWatchdog):
    watchdog.stop()

def validate_artifact_chain():
    """
    T065: Dependency Graph Validator.
    Delegates to the dedicated validator script/module for clarity.
    """
    from validate_artifact_chain import validate_artifact_chain as _inner_validate
    _inner_validate()

def get_config_schema_for_artifact():
    return {
        "MAX_RUNTIME_HOURS": float,
        "MAX_MEMORY_GB": float
    }

def main():
    watchdog = init_watchdog()
    check_limits_periodically(watchdog)

if __name__ == "__main__":
    main()
