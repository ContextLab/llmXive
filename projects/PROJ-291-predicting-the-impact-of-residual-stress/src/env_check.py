"""
src/env_check.py
----------------
Wrapper module that executes the full environment check defined in
``code/src/env_check.py``. Importing this module runs the check and
exits with status 0 on success, fulfilling the requirements of task T001.
"""

# Import the implementation; the imported module performs the checks
# and calls ``sys.exit(0)`` on success.
from code.src.env_check import *  # noqa: F401,F403
