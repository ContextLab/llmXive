"""
Compatibility shim for environments where the standard library ``subprocess``
module is shadowed or incomplete.  The test runner (pytest) expects the
attribute ``subprocess.PIPE``; if the real module is unavailable this shim
forwards all attribute access to the genuine stdlib implementation and
explicitly defines ``PIPE``.
"""
import importlib
import sys
from types import ModuleType

# Load the real stdlib subprocess module under a private name.
_real_subprocess: ModuleType = importlib.import_module("subprocess")

# Re‑export the most commonly used symbols.
PIPE = _real_subprocess.PIPE
STDOUT = _real_subprocess.STDOUT
CalledProcessError = _real_subprocess.CalledProcessError
run = _real_subprocess.run
Popen = _real_subprocess.Popen
CompletedProcess = _real_subprocess.CompletedProcess

def __getattr__(name):
    """Delegate any unknown attribute to the real subprocess module."""
    return getattr(_real_subprocess, name)

# Ensure ``import subprocess`` gives this shim.
sys.modules[__name__] = sys.modules[__name__]   # noqa: B018
