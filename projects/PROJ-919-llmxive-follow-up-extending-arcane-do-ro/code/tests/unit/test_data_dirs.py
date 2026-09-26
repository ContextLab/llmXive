"""
Legacy test file for data directories - kept for compatibility.
Merged logic into test_setup_data_dirs.py.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Import the actual test class from the new file
from tests.unit.test_setup_data_dirs import TestDataDirectories as TestDataDirectories

# Re-export for backward compatibility if other tests import this
__all__ = ["TestDataDirectories"]