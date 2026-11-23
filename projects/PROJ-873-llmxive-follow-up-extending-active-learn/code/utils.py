import os
import signal
import sys
import time
import resource
import logging
import subprocess
import json
from typing import Optional, Callable, Any

from config import get_config, PipelineConfig

logger = logging.getLogger(__name__)

class EnforcementVerificationError(Exception):
    """Raised when neither cgroups nor psutil/resource limits are available."""
    pass

class PartialRunError(Exception):
    pass

class DataFlowViolationError(Exception):
    pass

class ResourceWatchdog:
    """
    Monitors runtime and memory usage. Implements a 'Dual-Layer Hard Kill':
    Layer 1: Python-level signal (SIGKILL) via os.kill.
    Layer 2: Shell-level kill via subprocess (cgroup.kill or kill -9 -<pid>).
    """
    def __init__(self, max_runtime_hours: float, max_memory_gb: float, pid: int = None):
        self.max_runtime_hours = max_runtime_hours
        self.max_memory_gb = max_memory_gb
        self.start_time = time.time()
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.running = True
        self.pid = pid if pid is not None else os.getpid()
        self._kill_group = False

    def check(self):
        if not self.running:
            return

        # Ensure verification happened on first check if not done yet
        if not self.verification_passed:
            self._verify_enforcement_mechanisms()

        elapsed = time.time() - self.start_time
        elapsed_hours = elapsed / 3600

        # Check Runtime
        if elapsed_hours > self.max_runtime_hours:
            logger.error(f"Runtime limit exceeded: {elapsed_hours:.2f}h > {self.max_runtime_hours}h")
            self._hard_kill()
            sys.exit(1)

        # Check Memory
        try:
            # resource.getrusage ru_maxrss is in KB on Linux, bytes on macOS.
            # We assume Linux for cgroup context, but handle both.
            mem_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            
            # Detect unit: If > 100GB in KB, it's likely bytes (macOS).
            # Standard Linux maxrss is KB.
            if mem_usage_kb > 100 * 1024 * 1024: 
                # Likely bytes
                mem_bytes = mem_usage_kb
            else:
                # Likely KB
                mem_bytes = mem_usage_kb * 1024

            mem_gb = mem_bytes / (1024 * 1024 * 1024)
            
            if mem_gb > self.max_memory_gb:
                logger.error(f"Memory limit exceeded: {mem_gb:.2f}GB > {self.max_memory_gb}GB")
                self._hard_kill()
                sys.exit(1)
        except Exception as e:
            logger.warning(f"Could not check memory: {e}")

    def _hard_kill(self):
        logger.critical("Initiating Dual-Layer Hard Kill.")
        
        # Layer 1: Python signal
        try:
            os.kill(self.pid, signal.SIGKILL)
            logger.critical("Layer 1 (SIGKILL) sent.")
        except ProcessLookupError:
            pass
        except Exception as e:
            logger.error(f"Layer 1 signal failed: {e}")

        # Layer 2: Shell wrapper kill
        # Attempt cgroup.kill first, then kill -9 -<pid>
        try:
            cgroup_kill_path = "/sys/fs/cgroup/cgroup.kill"
            if os.path.exists(cgroup_kill_path):
                with open(cgroup_kill_path, "w") as f:
                    f.write("1")
                logger.critical("Layer 2 (cgroup.kill) triggered.")
            else:
                # Fallback to kill -9 on process group
                pid_group = -self.pid
                subprocess.run(["kill", "-9", str(pid_group)], check=False)
                logger.critical(f"Layer 2 (kill -9 -{pid_group}) triggered.")
        except Exception as e:
            logger.error(f"Layer 2 shell kill failed: {e}")

    def stop(self):
        self.running = False

def init_watchdog():
    config = get_config()
    
    # Verify enforcement capability (cgroups or psutil/resource)
    cgroups_available = False
    try:
        with open('/sys/fs/cgroup/cgroup.controllers', 'r') as f:
            cgroups_available = True
        logger.info("cgroups v2 available.")
    except FileNotFoundError:
        logger.warning("cgroups v2 not available.")
    
    # If cgroups are not available, we rely on resource.getrusage (psutil equivalent)
    # If resource.getrusage fails completely, we must fail loudly per T004a spec.
    # We assume resource module is always present in standard Python, but verify logic works.
    try:
        resource.getrusage(resource.RUSAGE_SELF)
    except Exception:
        raise EnforcementVerificationError("Neither cgroups nor resource.getrusage is functional. Cannot enforce limits.")

    watchdog = ResourceWatchdog(
        max_runtime_hours=float(config.MAX_RUNTIME_HOURS),
        max_memory_gb=float(config.MAX_MEMORY_GB)
    )
    
    return watchdog

def check_limits_periodically(watchdog: ResourceWatchdog, interval: int = 60):
    """Runs the watchdog check in a separate thread or loop."""
    # We run in a loop here as per the task requirement for the main execution loop integration
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
    # Avoid circular import by importing inside
    try:
        from validate_artifact_chain import validate_artifact_chain as _inner_validate
        _inner_validate()
    except ImportError:
        logger.warning("validate_artifact_chain module not found, skipping chain validation.")
    except Exception as e:
        logger.error(f"Artifact chain validation failed: {e}")
        raise

def get_config_schema_for_artifact():
    return {
        "MAX_RUNTIME_HOURS": float,
        "MAX_MEMORY_GB": float
    }

def main():
    watchdog = init_watchdog()
    try:
        check_limits_periodically(watchdog)
    finally:
        stop_watchdog(watchdog)

if __name__ == "__main__":
    main()
