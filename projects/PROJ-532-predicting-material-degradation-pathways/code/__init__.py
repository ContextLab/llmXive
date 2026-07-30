"""
LLMXive Material Degradation Pipeline Code Module.

This module provides the core implementation for predicting material
degradation pathways from compositional data.
"""
import os
import sys
from pathlib import Path

# Ensure the parent directory of this package is in sys.path
# so that 'code' can be imported as a top-level module
# when running scripts from the project root or other locations.
_current_dir = Path(__file__).resolve().parent
_parent_dir = _current_dir.parent

if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

# Explicitly set the PYTHONPATH environment variable for subprocesses
# and for consistency across the execution environment.
current_env_path = os.environ.get("PYTHONPATH", "")
if str(_parent_dir) not in current_env_path:
    if current_env_path:
        os.environ["PYTHONPATH"] = f"{_parent_dir}{os.pathsep}{current_env_path}"
    else:
        os.environ["PYTHONPATH"] = str(_parent_dir)

# Log the configuration for debugging purposes
import logging
logger = logging.getLogger(__name__)
logger.info(f"code/ module initialized. PYTHONPATH updated to include: {_parent_dir}")
