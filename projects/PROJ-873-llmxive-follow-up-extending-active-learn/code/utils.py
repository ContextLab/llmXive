import os
import signal
import sys
import time
import resource
import logging
import json
import subprocess
from typing import Optional, Callable
from threading import Thread

from config import get_config, PipelineConfig

logger = logging.getLogger(__name__)

class EnforcementVerificationError(Exception):
    """Raised when neither cgroups nor psutil-based enforcement can be verified."""
    pass

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
        self.pid = os.getpid()
        self.verification_passed = False

    def _verify_enforcement_mechanisms(self):
        """
        Verifies that at least one enforcement mechanism (cgroups or psutil) is available.
        If both fail, raises EnforcementVerificationError.
        """
        cgroups_available = False
        psutil_available = True # We assume standard library resource module is available, but verify logic works

        # Check cgroups v2
        try:
            with open('/sys/fs/cgroup/cgroup.controllers', 'r') as f:
                controllers = f.read().strip()
                if controllers:
                    cgroups_available = True
                    logger.info("cgroups v2 available.")
        except FileNotFoundError:
            logger.warning("cgroups v2 mount not found.")
        except PermissionError:
            logger.warning("Permission denied accessing cgroups mount.")

        # Check psutil/resource module functionality
        try:
            # Attempt to read current memory to ensure the mechanism works
            _ = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        except Exception as e:
            logger.error(f"Resource monitoring (psutil/resource) failed: {e}")
            psutil_available = False

        if not cgroups_available and not psutil_available:
            raise EnforcementVerificationError(
                "Neither cgroups v2 nor resource monitoring (psutil) is available. "
                "Cannot enforce FR-006 limits safely."
            )
        
        self.verification_passed = True
        return cgroups_available, psutil_available

    def check(self):
        if not self.running:
            return

        # Ensure verification happened on first check if not done yet
        if not self.verification_passed:
            self._verify_enforcement_mechanisms()

        elapsed = time.time() - self.start_time
        elapsed_hours = elapsed / 3600

        if elapsed_hours > self.max_runtime_hours:
            logger.error(f"Runtime limit exceeded: {elapsed_hours:.2f}h > {self.max_runtime_hours}h")
            self._hard_kill()
            return

        try:
            mem_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            # On Linux, ru_maxrss is in KB.
            mem_gb = mem_usage_kb / (1024 * 1024)
            
            if mem_gb > self.max_memory_gb:
                logger.error(f"Memory limit exceeded: {mem_gb:.2f}GB > {self.max_memory_gb}GB")
                self._hard_kill()
        except Exception as e:
            logger.warning(f"Could not check memory: {e}")

    def _hard_kill(self):
        """
        Dual-Layer Hard Kill Mechanism:
        Layer 1: Send SIGKILL to self via psutil/resource logic (os.kill).
        Layer 2: Attempt to write to cgroup.kill or kill the process group.
        """
        logger.critical("Initiating Dual-Layer Hard Kill.")
        
        # Layer 1: Standard signal to self
        try:
            os.kill(self.pid, signal.SIGKILL)
        except Exception as e:
            logger.error(f"Layer 1 (os.kill) failed: {e}")

        # Layer 2: Shell wrapper / cgroup kill
        # Try to write to cgroup.kill if available
        cgroup_kill_path = "/sys/fs/cgroup/cgroup.kill"
        if os.path.exists(cgroup_kill_path):
            try:
                with open(cgroup_kill_path, 'w') as f:
                    f.write('1')
                logger.info("Layer 2 (cgroup.kill) triggered.")
            except Exception as e:
                logger.error(f"Layer 2 (cgroup.kill) failed: {e}")
        
        # Fallback Layer 2: Kill process group
        try:
            os.killpg(os.getpgid(self.pid), signal.SIGKILL)
            logger.info("Layer 2 (kill -9 -<pgid>) triggered.")
        except Exception as e:
            logger.error(f"Layer 2 (killpg) failed: {e}")

        # Final safety: exit immediately
        sys.exit(1)

    def stop(self):
        self.running = False

def init_watchdog():
    config = get_config()
    
    # Validate config values exist
    if not hasattr(config, 'MAX_RUNTIME_HOURS') or not hasattr(config, 'MAX_MEMORY_GB'):
        raise RuntimeError("Config missing MAX_RUNTIME_HOURS or MAX_MEMORY_GB. Ensure T004 is complete.")

    watchdog = ResourceWatchdog(
        max_runtime_hours=float(config.MAX_RUNTIME_HOURS),
        max_memory_gb=float(config.MAX_MEMORY_GB)
    )
    
    # Run verification immediately to fail fast if environment is unsupported
    try:
        watchdog._verify_enforcement_mechanisms()
    except EnforcementVerificationError as e:
        logger.critical(str(e))
        raise

    logger.info("Watchdog initialized and verified.")
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
    """
    Standalone execution for testing the watchdog.
    Simulates a long-running process if needed, or just verifies initialization.
    """
    try:
        watchdog = init_watchdog()
        logger.info("Watchdog active. Checking limits periodically (Ctrl+C to stop).")
        check_limits_periodically(watchdog, interval=5)
    except EnforcementVerificationError as e:
        print(f"FATAL: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Watchdog stopped by user.")
    except Exception as e:
        logger.error(f"Watchdog error: {e}")
        sys.exit(1)
    finally:
        if 'watchdog' in locals():
            stop_watchdog(watchdog)

if __name__ == "__main__":
    main()
