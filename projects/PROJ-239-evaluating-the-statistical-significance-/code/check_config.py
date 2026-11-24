"""
Simple sanity check script for the updated config module.

It imports ``code.config`` and calls ``validate_config()`` without
arguments, which should succeed using the default configuration.
The script exits with status 0 on success, otherwise the exception
propagates and the process exits with a non‑zero code.
"""
import sys

# Import the config module from the package
from code import config as cfg

try:
    # This should succeed using the default configuration
    cfg.validate_config()
except Exception as e:
    sys.stderr.write(f"Validation failed: {e}\\n")
    sys.exit(1)

# If we reach here, validation succeeded
sys.exit(0)