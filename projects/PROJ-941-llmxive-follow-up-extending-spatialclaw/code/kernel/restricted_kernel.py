import sys
import builtins
import logging
import traceback
import os
import time
from types import ModuleType
from typing import Optional, Set, Dict, Any

from kernel.blockers import RestrictedActionError, check_library_policy

# Configure logger for the kernel
logger = logging.getLogger(__name__)

# Global state for the kernel
_kernel_instance: Optional['RestrictedKernel'] = None
_policy_active: bool = False

# Path for blocked operations log
BLOCKED_LOG_PATH = "results/logs/blocked_operations.log"

def _ensure_log_directory():
    """Ensure the directory for the blocked operations log exists."""
    log_dir = os.path.dirname(BLOCKED_LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

def _log_blocked_operation(module_name: str, error: Exception):
    """
    Log a blocked operation to the blocked_operations.log file.
    Includes full call stack with line numbers and function names.
    """
    _ensure_log_directory()
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    # Get the full stack trace
    stack_trace = traceback.format_exc()
    
    # Format the log entry
    log_entry = (
        f"[{timestamp}] BLOCKED IMPORT: {module_name}\n"
        f"Error: {type(error).__name__}: {error}\n"
        f"Stack Trace:\n{stack_trace}\n"
        f"{'='*80}\n"
    )
    
    try:
        with open(BLOCKED_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except IOError as e:
        logger.error(f"Failed to write to blocked operations log: {e}")

class RestrictedImportHook:
    """
    A meta-path importer hook that intercepts module imports and blocks
    specific libraries defined in the policy.
    """
    def __init__(self, blocked_modules: Set[str]):
        self.blocked_modules = blocked_modules

    def find_module(self, fullname: str, path=None):
        # Check if this module is blocked
        if any(fullname == blocked or fullname.startswith(blocked + ".") 
               for blocked in self.blocked_modules):
            return self
        return None

    def load_module(self, fullname: str):
        # This should not be reached due to find_module logic,
        # but included for safety if logic changes
        if fullname in self.blocked_modules:
            raise RestrictedActionError(f"Import of blocked library '{fullname}' is not allowed.")
        return None

    def create_module(self, spec):
        # Called for Python 3.4+
        if any(spec.name == blocked or spec.name.startswith(blocked + ".") 
               for blocked in self.blocked_modules):
            raise RestrictedActionError(f"Import of blocked library '{spec.name}' is not allowed.")
        return None

    def exec_module(self, module):
        # Called for Python 3.4+
        if any(module.__name__ == blocked or module.__name__.startswith(blocked + ".") 
               for blocked in self.blocked_modules):
            raise RestrictedActionError(f"Import of blocked library '{module.__name__}' is not allowed.")

class RestrictedKernel:
    """
    Manages the enforcement of the 2D action space policy.
    """
    def __init__(self, blocked_modules: Set[str]):
        self.blocked_modules = blocked_modules
        self.hook: Optional[RestrictedImportHook] = None
        self._original_import = builtins.__import__

    def activate(self):
        """Activate the restricted kernel by installing import hooks."""
        global _policy_active
        if _policy_active:
            logger.warning("Restricted kernel is already active.")
            return

        logger.info(f"Activating RestrictedKernel. Blocking: {self.blocked_modules}")
        
        # Install the import hook
        self.hook = RestrictedImportHook(self.blocked_modules)
        sys.meta_path.insert(0, self.hook)
        
        # Wrap __import__ for additional safety (optional, but good for dynamic imports)
        # Note: sys.meta_path is usually sufficient for standard imports
        
        _policy_active = True
        logger.info("RestrictedKernel activated.")

    def deactivate(self):
        """Deactivate the restricted kernel by removing import hooks."""
        global _policy_active
        if not _policy_active:
            logger.warning("RestrictedKernel is not active.")
            return

        logger.info("Deactivating RestrictedKernel.")
        
        if self.hook and self.hook in sys.meta_path:
            sys.meta_path.remove(self.hook)
            self.hook = None
        
        _policy_active = False
        logger.info("RestrictedKernel deactivated.")

def get_kernel() -> Optional[RestrictedKernel]:
    """Get the current active kernel instance."""
    return _kernel_instance

def enforce_2d_policy(blocked_modules: Optional[Set[str]] = None):
    """
    Enforce the 2D policy by creating and activating a RestrictedKernel.
    Uses default blocked modules if none provided.
    """
    global _kernel_instance
    
    if blocked_modules is None:
        # Default blocked modules based on project constraints
        blocked_modules = {"trimesh", "pytorch3d", "open3d", "torch3d"}
    
    _kernel_instance = RestrictedKernel(blocked_modules)
    _kernel_instance.activate()
    logger.info(f"Enforced 2D policy with blocked modules: {blocked_modules}")

def release_2d_policy():
    """Release the 2D policy by deactivating the kernel."""
    global _kernel_instance
    if _kernel_instance:
        _kernel_instance.deactivate()
        _kernel_instance = None
        logger.info("Released 2D policy.")

# Monkey-patch __import__ to catch dynamic imports and log stack traces
_original_import = builtins.__import__

def _restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
    """
    Custom import function that checks against the policy and logs
    the full call stack if a blocked module is attempted.
    """
    # Check if the kernel is active
    if not _policy_active:
        return _original_import(name, globals, locals, fromlist, level)

    # Check against blocked modules
    blocked_modules = _kernel_instance.blocked_modules if _kernel_instance else set()
    
    if any(name == blocked or name.startswith(blocked + ".") 
           for blocked in blocked_modules):
        # Create a detailed error
        error_msg = f"Import of blocked library '{name}' is not allowed."
        error = RestrictedActionError(error_msg)
        
        # Log the blocked operation with stack trace
        _log_blocked_operation(name, error)
        
        # Raise the error
        raise error

    return _original_import(name, globals, locals, fromlist, level)

# Apply the monkey patch if the kernel is active
def _update_import_hook():
    if _policy_active:
        builtins.__import__ = _restricted_import
    else:
        builtins.__import__ = _original_import

# Override activate/deactivate to also update the __import__ hook
original_activate = RestrictedKernel.activate
original_deactivate = RestrictedKernel.deactivate

def custom_activate(self):
    original_activate(self)
    _update_import_hook()

def custom_deactivate(self):
    original_deactivate(self)
    _update_import_hook()

RestrictedKernel.activate = custom_activate
RestrictedKernel.deactivate = custom_deactivate