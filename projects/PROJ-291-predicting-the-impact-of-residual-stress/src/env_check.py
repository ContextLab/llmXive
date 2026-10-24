"""
src/env_check.py
----------------
Minimal wrapper that re-exports the implementation from
``code/src/env_check.py``.  The original implementation performs the
environment checks, writes the checksums, prints a success message and
exits with status 0.  Importing it as a module (``python -m src.env_check``)
therefore runs the checks and terminates cleanly.
"""

# Re-export everything from the actual implementation.
from code.src.env_check import *  # noqa: F401,F403

# No additional logic is required; the imported module runs on import
# and calls ``sys.exit(0)`` on success.  Keeping this file minimal avoids
# the previous recursive import that caused a failure.