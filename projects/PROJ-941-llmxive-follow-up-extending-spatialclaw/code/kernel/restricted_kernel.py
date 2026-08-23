"""
Restricted Kernel Implementation for enforcing 2D spatial constraints.

This module provides the RestrictedKernel class and hooks to intercept imports
and function calls, ensuring that only 2D-safe libraries (shapely, numpy) are used
while blocking 3D libraries (trimesh, pytorch3d, open3d).
"""
import sys
import builtins
import logging
import traceback
import os
from types import ModuleType
from typing import Callable, Optional, Set, List
from contextlib import contextmanager

from kernel.blockers import RestrictedActionError, check_library_policy

logger = logging.getLogger(__name__)

# Global state for the kernel
_kernel_instance: Optional['RestrictedKernel'] = None
_policy_active: bool = False

# Path for the blocked operations log
BLOCKED_LOG_PATH = "results/logs/blocked_operations.log"


def _ensure_log_directory():
    """Ensure the results/logs directory exists."""
    log_dir = os.path.dirname(BLOCKED_LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)


def _log_blocked_operation(name: str, stack_trace: str):
    """
    Logs the blocked import attempt and its full stack trace to the dedicated log file.
    """
    _ensure_log_directory()
    timestamp = logging.Formatter('%(asctime)s').format(logging.LogRecord(
        name='root', level=logging.INFO, pathname='', lineno=0,
        msg='', args=(), exc_info=None
    ))
    
    log_entry = (
        f"--- BLOCKED IMPORT ATTEMPT ---\n"
        f"Timestamp: {timestamp}\n"
        f"Blocked Module: {name}\n"
        f"Call Stack:\n{stack_trace}\n"
        f"-----------------------------\n"
    )
    
    try:
        with open(BLOCKED_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        logger.warning(f"Blocked import '{name}' logged to {BLOCKED_LOG_PATH}")
    except IOError as e:
        logger.error(f"Failed to write blocked operation log: {e}")


class RestrictedImportHook:
    """
    A meta-path finder that intercepts import statements to enforce the 2D policy.
    """
    def __init__(self, blocked_libraries: Set[str]):
        self.blocked_libraries = blocked_libraries
        self._original_import = builtins.__import__

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        # Check if the requested module is in the blocked list
        # We check the top-level module name (split by '.')
        top_level = name.split('.')[0]
        
        if top_level in self.blocked_libraries:
            # Capture the full call stack
            stack_trace = ''.join(traceback.format_stack())
            
            # Log the blocked operation with full context to the dedicated file
            _log_blocked_operation(name, stack_trace)
            
            # Log to standard logger as well for immediate visibility
            logger.warning(f"BLOCKED IMPORT attempt: {name}")
            logger.warning(f"Traceback at block:\n{stack_trace}")
            
            raise RestrictedActionError(
                f"Import of '{name}' is blocked by the 2D spatial restriction policy. "
                f"Use only 2D-safe libraries (e.g., shapely, numpy). "
                f"Full stack trace logged to {BLOCKED_LOG_PATH}."
            )
        
        # If not blocked, proceed with normal import
        return self._original_import(name, globals, locals, fromlist, level)


class RestrictedKernel:
    """
    Core kernel that manages the restricted environment.
    """
    def __init__(self, blocked_libraries: Optional[Set[str]] = None):
        if blocked_libraries is None:
            # Default blocked libraries as per spec
            blocked_libraries = {"trimesh", "pytorch3d", "open3d", "pyglet", "pygame"}
        
        self.blocked_libraries = blocked_libraries
        self.hook = RestrictedImportHook(self.blocked_libraries)
        self._installed = False

    def install(self):
        """Install the import hook to start blocking imports."""
        if not self._installed:
            # Register the hook at the beginning of meta_path
            sys.meta_path.insert(0, self.hook)
            self._installed = True
            logger.info("RestrictedKernel: Import hook installed.")
        else:
            logger.debug("RestrictedKernel: Hook already installed.")

    def uninstall(self):
        """Remove the import hook."""
        if self._installed:
            try:
                sys.meta_path.remove(self.hook)
                self._installed = False
                logger.info("RestrictedKernel: Import hook uninstalled.")
            except ValueError:
                logger.warning("RestrictedKernel: Hook was not found in meta_path.")

    def execute(self, func: Callable, *args, **kwargs):
        """
        Execute a function within the restricted kernel context.
        Ensures the hook is active during execution.
        """
        if not self._installed:
            self.install()
        
        try:
            return func(*args, **kwargs)
        except RestrictedActionError:
            # Re-raise restricted errors immediately
            raise
        except Exception as e:
            # Log other errors but do not suppress them
            logger.error(f"Error during execution in restricted kernel: {e}")
            raise

def get_kernel() -> RestrictedKernel:
    """Get or create the singleton kernel instance."""
    global _kernel_instance
    if _kernel_instance is None:
        _kernel_instance = RestrictedKernel()
    return _kernel_instance

@contextmanager
def enforce_2d_policy():
    """
    Context manager to enforce 2D policy for a block of code.
    Returns the kernel instance.
    """
    kernel = get_kernel()
    kernel.install()
    global _policy_active
    _policy_active = True
    try:
        yield kernel
    finally:
        kernel.uninstall()
        _policy_active = False

def release_2d_policy():
    """Explicitly release the policy (removes hook)."""
    kernel = get_kernel()
    kernel.uninstall()
    global _policy_active
    _policy_active = False

# Convenience functions for direct usage
def enforce_2d_policy():
    """
    Enforces the 2D policy globally by installing the import hook.
    Returns the kernel instance.
    """
    kernel = get_kernel()
    kernel.install()
    global _policy_active
    _policy_active = True
    return kernel

def release_2d_policy():
    """
    Releases the 2D policy by uninstalling the import hook.
    """
    kernel = get_kernel()
    kernel.uninstall()
    global _policy_active
    _policy_active = False

# Patch the module level to match the API surface required by tasks
# The API surface expects these specific functions to be available at module level.
# We redefine them here to ensure they are the active ones.

def enforce_2d_policy():
    """
    Global function to enforce the 2D policy.
    """
    kernel = get_kernel()
    kernel.install()
    global _policy_active
    _policy_active = True
    return kernel

def release_2d_policy():
    """
    Global function to release the 2D policy.
    """
    kernel = get_kernel()
    kernel.uninstall()
    global _policy_active
    _policy_active = False